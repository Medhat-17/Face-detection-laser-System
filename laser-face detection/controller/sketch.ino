// controller/controller.cpp
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <chrono>
#include <cstring>
#include <iostream>
#include <sstream>
#include <string>
#include <thread>
#include <mutex>
#include <cmath>

using clock_t = std::chrono::steady_clock;

struct State {
    double pan = 0.0;    // degrees
    double tilt = 0.0;   // degrees
    int laser = 0;       // 0/1
    std::mutex m;
};

int main() {
    const int port = 9000;
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd == -1) { perror("socket"); return 1; }

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(port);
    if (bind(server_fd, (sockaddr*)&addr, sizeof(addr)) < 0) { perror("bind"); return 1; }
    if (listen(server_fd, 1) < 0) { perror("listen"); return 1; }

    std::cout << "Controller listening on port " << port << "...\n";

    State st;
    double target_pan = 0.0, target_tilt = 0.0;
    int target_laser = 0;

    // Dynamics thread: moves actual pan/tilt towards target smoothly.
    std::thread dynamics([&](){
        double sim_dt = 0.02; // 50 Hz
        while (true) {
            {
                std::lock_guard<std::mutex> lk(st.m);
                double alpha = 1.0 - std::exp(-sim_dt*6.0); // first-order time constant
                st.pan += (target_pan - st.pan) * alpha;
                st.tilt += (target_tilt - st.tilt) * alpha;
                st.laser = target_laser;
            }
            std::this_thread::sleep_for(std::chrono::duration<double>(sim_dt));
        }
    });

    while (true) {
        int client = accept(server_fd, nullptr, nullptr);
        if (client < 0) { perror("accept"); continue; }
        std::cout << "Client connected\n";

        // Per-connection loop
        char buf[1024];
        while (true) {
            ssize_t n = recv(client, buf, sizeof(buf)-1, 0);
            if (n <= 0) { std::cout << "Client disconnected\n"; close(client); break; }
            buf[n] = 0;
            std::istringstream iss(buf);
            std::string line;
            while (std::getline(iss, line)) {
                if (line.size() == 0) continue;
                std::istringstream ls(line);
                std::string cmd;
                ls >> cmd;
                if (cmd == "SET") {
                    double p, t; int l;
                    if (!(ls >> p >> t >> l)) {
                        std::string err = "ERR bad SET\n";
                        send(client, err.c_str(), err.size(), 0);
                        continue;
                    }
                    // clamp
                    if (p < -180) p = -180; if (p > 180) p = 180;
                    if (t < -90) t = -90; if (t > 90) t = 90;
                    if (l != 0) l = 1;
                    target_pan = p; target_tilt = t; target_laser = l;

                    std::string ok = "OK\n";
                    send(client, ok.c_str(), ok.size(), 0);
                    // also send immediate telemetry
                    std::ostringstream out;
                    {
                        std::lock_guard<std::mutex> lk(st.m);
                        out << "POS " << st.pan << " " << st.tilt << " " << st.laser << "\n";
                    }
                    std::string o = out.str();
                    send(client, o.c_str(), o.size(), 0);
                } else if (cmd == "PING") {
                    std::string ok = "PONG\n";
                    send(client, ok.c_str(), ok.size(), 0);
                } else if (cmd == "GET") {
                    std::ostringstream out;
                    {
                        std::lock_guard<std::mutex> lk(st.m);
                        out << "POS " << st.pan << " " << st.tilt << " " << st.laser << "\n";
                    }
                    std::string o = out.str();
                    send(client, o.c_str(), o.size(), 0);
                } else {
                    std::string err = "ERR unknown\n";
                    send(client, err.c_str(), err.size(), 0);
                }
            }
        }
    }

    dynamics.join();
    close(server_fd);
    return 0;
}

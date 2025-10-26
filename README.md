The Face-Detection Laser System is a high-precision mechatronic architecture integrating real-time computer vision, control theory, and low-level embedded interfacing to achieve autonomous facial recognition and laser actuation within a closed-loop AI–robotic feedback pipeline. The system uses a Python–C++ infrastructure, where TensorFlow-based neural inference operates on live video frames streamed through OpenCV, performing convolutional face detection using bounding-box regression. Each detected facial centroid is projected from pixel coordinates into the physical actuation space using a calibrated camera model derived from intrinsic and extrinsic parameters, generating angular displacement values (Δθx, Δθy) that represent the positional offset between the optical axis and the target. These spatial coordinates are processed through a PID controller, implemented in C++ for low-latency response, providing fine-grained servo angular adjustments by minimizing the real-time error through proportional–integral–derivative correction. The controller operates at a 1 kHz loop frequency synchronized through serial or TCP communication, ensuring deterministic motion with less than 3 ms delay. The virtual laser subsystem renders beam trajectories using subpixel interpolation and Gaussian intensity decay modeling, allowing optical path simulation that follows both camera geometry and actuator dynamics. On the inference side, TensorFlow performs optimized model execution with float16 quantization and GPU acceleration, achieving frame rates over 60 FPS while maintaining accuracy under varying lighting through adaptive histogram equalization and noise normalization. All system states—camera input, controller output, tracking error, and detection confidence—are logged for real-time visualization through a Python-based interface using Matplotlib and Tkinter, enabling parameter tuning and control gain calibration. The result is a complete AI-driven mechatronic system combining vision-based sensing, servo control, and real-time computation, capable of precise laser alignment, predictive target tracking, and synchronous sensor–actuator coordination using multi-threaded programming.

# Features

Real-time face detection using TensorFlow and OpenCV.

Pixel-to-angle mapping via calibrated camera intrinsics and extrinsics.

PID-based servo control implemented in C++ at 1 kHz loop frequency.

Virtual laser rendering with subpixel interpolation and Gaussian decay.

TensorFlow optimizations: float16 quantization and GPU acceleration.

Adaptive preprocessing: histogram equalization and noise normalization.

Continuous logging of sensor and control telemetry; live visualization and parameter tuning via Matplotlib/Tkinter.

Modular codebase: replaceable detection model and controller backend.





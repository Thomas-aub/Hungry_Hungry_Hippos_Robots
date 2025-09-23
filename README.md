# 🦛 Hungry Hungry Hippos Robot Game  

## Project Overview  
Hungry Hungry Hippos Robot Game is an advanced robotics and control systems project inspired by the classic tabletop game. The system features two autonomous robots that compete to collect as many balls as possible in a limited time, leveraging real-time computer vision, networked control, and modular software design. This project demonstrates practical applications in robotics, distributed systems, and machine learning.  

## Key Features
- **Autonomous Multi-Robot System:** Two Lego EV3 robots, each controlled by a Raspberry Pi, operate independently to maximize ball collection.  
- **Real-Time Computer Vision:** Overhead cameras track the arena and provide live video streams for object detection and localization.  
- **Networked Communication:** Robust TCP/IP networking enables reliable command and data exchange between the control system and robots.  
- **Python & C++ Codebase:** Modular, extensible code written in Python (with C++ components) for rapid prototyping and integration with ML libraries.  
- **ML/AI Ready:** The architecture is designed for easy integration of machine learning algorithms, such as reinforcement learning or computer vision models, to enable autonomous decision-making and adaptive strategies.  

## Technical Details  
- **Robots:** 2 autonomous Lego EV3 robots  
- **Programming Languages:** Python & C++  
- **Computing Unit:** Raspberry Pi (per robot)  
- **Vision System:**  
  - Two overhead cameras track the game arena  
  - Video stream transmitted over a private Wi-Fi network  
  - Raspberry Pi processes images and sends movement commands to robots  
- **Game Setup:**  
  - Balls are randomly dropped into the arena  
  - Robots must identify and collect them as fast as possible  

## Applications
- Robotics competitions and demonstrations  
- Research in multi-agent systems and distributed control  
- Prototyping for machine learning in robotics (e.g., imitation learning, RL)  
- Educational tool for networking, control, and Python programming  

## Technologies Used
- Python 3  
- C++  
- Raspberry Pi  
- OpenCV (for computer vision)  
- pynput (for manual control)  
- socket (for TCP networking)  

## Getting Started
1. Clone this repository  
2. Set up the Raspberry Pi and connect the Lego EV3 robots  
3. Configure the overhead cameras and Wi-Fi network  
4. Run the control scripts as described in the documentation  

## License
This project is for educational and research purposes.
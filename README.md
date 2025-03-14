# Awaken Monitoring System

A real-time monitoring system for individuals with ALS that uses computer vision to detect closed eyes and trigger an alert when necessary. This project leverages pre-trained Haar cascade models for face and eye detection, integrated with a user-friendly graphical interface.

---

## Project Overview

The Awaken Monitoring System is designed to improve nighttime safety for individuals with ALS by continuously monitoring their eye state in real time. When the system detects a prolonged closure of the eyes, it plays an alert sound (default: `song.mp3`) to notify caregivers. The system is built using computer vision techniques combined with a trained model for enhanced detection accuracy.

---

## Repository Contents

- **`cv_close_eyes_detect.py`**  
  The primary computer vision script that captures video input, processes each frame to detect faces and eyes using Haar cascade XML models, and identifies closed eyes.

- **`gui_app.py`**  
  The graphical user interface (GUI) script that provides real-time monitoring, system controls, and displays the detection results, making it easy for caregivers to interact with the system.

- **`song.mp3`**  
  The alert sound file that is played when the system detects an alert condition. This file is changeable, allowing users to customize the alert tone.

- **XML Files (e.g., `haarcascade_frontalface_alt.xml`, `haarcascade_eye_tree_eyeglasses.xml`)**  
  Pre-trained Haar cascade models used by the detection scripts for identifying facial features and eyes.

---

## Requirements

- Python 3.x
- OpenCV (`opencv-python`)
- Tkinter (typically bundled with Python)
- Pygame (if audio functionality is used)
- A compatible camera or webcam for real-time monitoring

---


This README provides an overview of the Awaken Monitoring System, details its core components, and outlines instructions for setup and use. Enjoy improving nighttime safety with our practical, user-friendly technology!

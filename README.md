# Lattice Radiotherapy Auto-Contouring System
# Lattice Radiotherapy 自動化勾勒系統 (Varian Eclipse Compatible)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)]()
[![Status](https://img.shields.io/badge/Status-Stable-brightgreen)]()

> A standalone tool for automating Lattice Radiotherapy (LRT) contouring, specifically optimized for **Varian Eclipse TPS**.  
> 專為 **Varian Eclipse** 治療計畫系統設計的 Lattice 自動化勾勒工具。

---

## 📋 Table of Contents (目錄)
- [Introduction (簡介)](#-introduction-簡介)
- [Key Features (核心功能)](#-key-features-核心功能)
- [Installation (安裝)](#-installation-安裝)
- [Usage (使用說明)](#-usage-使用說明)
- [Screenshots (介面預覽)](#-screenshots-介面預覽)
- [Disclaimer (免責聲明)](#-disclaimer-免責聲明)

---

## 📖 Introduction (簡介)
This application automates the generation of high-dose lattice spheres within a PTV. It solves common DICOM compatibility issues encountered when importing external structures into **Varian Eclipse**, such as `VR DS` string length errors and geometry validity checks.

本系統解決了外部結構匯入 Varian Eclipse 時常見的相容性問題（如 `VR DS` 字串長度錯誤、輪廓點數不足），讓醫學物理師能快速生成標準化的 Lattice 計畫結構。

---

## ✨ Key Features (核心功能)
- **Eclipse-Ready DICOM Generation**: 
  - Auto-corrects decimal precision for valid `VR DS` tags.
  - Filters invalid contours (< 3 points).
  - Generates unique UIDs to prevent import conflicts.
- **Smart OAR Avoidance**: Select multiple OARs to automatically exclude them from the lattice structure.
- **Precise Geometry**: 
  - Supports **Cubic** and **Hexagonal (Staggered)** packing.
  - "Smart Margin" calculation ensures spheres stay strictly within the PTV.
- **Visualization**: Built-in 2D slice viewer with layer control.

---

## ⚙️ Installation (安裝)

### Method 1: Download Executable (Recommended for Clinical Users)
No Python installation required.
1. Go to the [Releases](../../releases) page.
2. Download the latest `LatticeRT_System.exe`.
3. Run the application directly.

### Method 2: Run from Source (For Developers)
```bash
# Clone this repository
git clone [https://github.com/chunting112190/Lattice-RT-Auto-Contouring.git](https://github.com/chunting112190/Lattice-RT-Auto-Contouring.git)

# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py


Usage (使用說明)
Load Files: Select your CT folder and RT Structure file.
Select Structures: Choose the target PTV and OARs to avoid (Hold Ctrl for multiple OARs).
Configure: Set Sphere Size (mm), Spacing (mm), and Margin (mm).
Generate: Click "Generate". The system will save a new DICOM file compatible with Eclipse.


Screenshots (介面預覽)


⚠️ Disclaimer (免責聲明)
This software is for research and educational purposes only. It has not been cleared by the FDA or other regulatory bodies for clinical use. Users must verify all generated contours before clinical application.

本軟體僅供研究與教育用途，未經 FDA 或衛福部核准用於臨床醫療行為。臨床使用前請務必進行驗證。

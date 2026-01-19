# Lattice Radiotherapy Auto-Contouring System
# Lattice Radiotherapy 自動化勾勒系統 (Varian Eclipse Compatible)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)]()
[![Status](https://img.shields.io/badge/Status-Stable-brightgreen)]()

> A standalone GUI tool for automating Lattice Radiotherapy (LRT) contouring, specifically optimized for **Varian Eclipse TPS**.  
> 專為 **Varian Eclipse** 治療計畫系統設計的 Lattice 自動化勾勒工具，解決 DICOM 匯入相容性問題。

---

## 📋 Table of Contents (目錄)
- [Introduction (簡介)](#-introduction-簡介)
- [Key Features (核心功能)](#-key-features-核心功能)
- [Installation (安裝)](#-installation-安裝)
- [Usage (使用說明)](#-usage-使用說明)
- [Screenshots (介面預覽)](#-screenshots-介面預覽)
- [Technical Details (技術細節)](#-technical-details-技術細節)
- [Disclaimer (免責聲明)](#-disclaimer-免責聲明)

---

## 📖 Introduction (簡介)

**English:**
This application is designed to automate the generation of high-dose lattice spheres (vertices) within a specified PTV for Lattice Radiotherapy (LRT). 

It addresses and resolves specific DICOM compatibility issues often encountered when importing external structures into **Varian Eclipse**, including:
1.  **`VR DS` errors**: Invalid string lengths for decimal coordinates.
2.  **Geometry errors**: Contours with less than 3 points.
3.  **UID collisions**: "Object Already Exists" errors during re-import.

**中文:**
本系統是一個獨立的 GUI 應用程式，旨在協助醫學物理師與放射腫瘤醫師快速在 PTV 內生成 Lattice 高劑量球體結構。

本工具特別針對 **Varian Eclipse** 治療計畫系統進行優化，解決了以下常見的匯入錯誤：
1.  **`VR DS` 格式錯誤**：自動修正座標小數點精度，符合 DICOM 標準。
2.  **幾何結構錯誤**：自動過濾點數不足 3 點的無效輪廓。
3.  **UID 衝突**：每次生成皆會產生全新的 UID，避免重複匯入時發生「物件已存在」的錯誤。

---

## ✨ Key Features (核心功能)

* **Eclipse-Ready DICOM Generation (完美相容 Eclipse)**
    * Generates standard DICOM RT Structure Sets compliant with Varian's import requirements.
    * Auto-correction of `DS` (Decimal String) value representation.
    * Automatic removal of artifacts and noise contours.

* **Smart OAR Avoidance (智慧危急器官避開)**
    * Allows selection of multiple OARs (Organs At Risk).
    * Automatically subtracts OAR volumes from the lattice generation region.

* **Precise Geometry Control (精確幾何控制)**
    * **Smart Margin**: Ensures spheres are strictly contained within the PTV based on radius + buffer.
    * **Packing Modes**: Supports both **Cubic (Standard)** and **Hexagonal (Staggered)** packing for optimal dose distribution.
    * **Physical Aspect Ratio**: Corrects for non-square pixel spacing to ensure perfect spheres.

* **Interactive Visualization (互動式視覺化)**
    * Built-in 2D slice viewer with correct aspect ratio rendering.
    * **Layer Control**: Toggle visibility of PTV (Blue), Lattice (Red), and OARs.

---

## ⚙️ Installation (安裝)

### Method 1: Standalone Executable (Recommended)
**方法一：下載執行檔 (推薦臨床使用者)**

No Python installation is required.
1.  Go to the [**Releases**](../../releases) page on the right sidebar.
2.  Download the latest `LatticeRT_System.exe`.
3.  Run the application directly on any Windows PC.

無需安裝 Python 環境，下載即用。
1.  前往右側的 [**Releases (發布版本)**](../../releases) 頁面。
2.  下載最新的 `LatticeRT_System.exe`。
3.  直接雙擊執行。

### Method 2: Run from Source (For Developers)
**方法二：從原始碼執行 (開發者用)**

1.  Clone the repository:
    ```bash
    git clone [https://github.com/YourUsername/Lattice-RT-Auto-Contouring.git](https://github.com/YourUsername/Lattice-RT-Auto-Contouring.git)
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the application:
    ```bash
    python main.py
    ```

---

## 🚀 Usage (使用說明)

1.  **Load Files (載入檔案)**:
    * Select the folder containing the CT series.
    * Select the existing RT Structure file (`.dcm`).
2.  **Structure Selection (結構選擇)**:
    * **Target PTV**: Select from the dropdown menu.
    * **Avoid OARs**: Select from the list (Hold `Ctrl` or `Shift` to select multiple organs).
3.  **Parameters (參數設定)**:
    * **Size (mm)**: Diameter of the lattice spheres.
    * **Spacing (mm)**: Center-to-center distance between spheres.
    * **Margin (mm)**: Buffer zone from the PTV boundary (Sphere radius + Buffer).
    * **Packing**: Choose between Cubic or Hexagonal.
4.  **Generate (生成)**:
    * Click the **Generate** button.
    * A visualization window will verify the result.
    * Import the generated file into Varian Eclipse.

---

## 📸 Screenshots (介面預覽)


![GUI Interface]([https://via.placeholder.com/800x500?text=GUI+Screenshot+Here](https://github.com/chunting112190/Lattice-RT-Auto-Contouring/blob/main/Home%20Page.png)]

---

## 🔧 Technical Details (技術細節)

* **Language**: Python 3.10+
* **GUI Framework**: Tkinter (Native Windows Interface)
* **Core Libraries**:
    * `pydicom`: DICOM I/O and tag manipulation.
    * `rt_utils`: Mask generation and contour conversion.
    * `scipy.ndimage`: Distance transform and morphology operations.
    * `matplotlib`: Medical image visualization.

---

## ⚠️ Disclaimer (免責聲明)

**English:**
This software is developed for **research and educational purposes only**. It has not been reviewed or approved by the FDA, TFDA, or any other regulatory agency for clinical use. The user assumes all responsibility for verifying the accuracy of the generated contours before using them in a clinical treatment plan.

**中文:**
本軟體僅供**研究與教育用途**。本工具尚未經美國 FDA、台灣衛福部 (TFDA) 或其他監管機構核准用於臨床醫療行為。使用者須自行承擔風險，並務必在臨床治療計畫使用前，由合格醫學物理師或醫師驗證生成的結構準確性。

---

© 2026 [Your Name / Organization]. All Rights Reserved.




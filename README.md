Lattice Radiotherapy Automation System (Varian Eclipse Compatible)
Lattice Radiotherapy 自動化勾勒系統 (Varian Eclipse 相容版)
📖 Introduction (簡介)
English: This is a standalone GUI application developed in Python to automate the contouring process for Lattice Radiotherapy (LRT). It imports CT images and generates lattice structures (high-dose spheres) within a specified PTV. The system is specifically optimized for Varian Eclipse TPS, solving common compatibility issues such as VR DS string length errors and contour point insufficiency.

中文: 這是一個基於 Python 開發的獨立 GUI 應用程式，旨在自動化 Lattice Radiotherapy (LRT) 的勾勒流程。系統可讀取 CT 影像，並在指定的 PTV 範圍內自動生成 Lattice 結構（高劑量球體）。本工具特別針對 Varian Eclipse 治療計畫系統 進行優化，解決了常見的 VR DS 字串長度錯誤及輪廓點數不足導致無法匯入的問題。

✨ Key Features (核心功能)
Varian Eclipse Compatibility Fixes (Varian Eclipse 相容性修正):

Auto-correction of decimal precision to prevent invalid for VR DS errors.

Automatic filtering of contours with less than 3 points to ensure valid ROI geometry.

Unique UID regeneration to prevent "Object Already Exists" collision errors.

Smart Margin & OAR Avoidance (智慧邊界與危急器官避開):

Supports selecting multiple OARs to automatically subtract them from the lattice generation area.

"Smart Margin" calculation ensures spheres are strictly contained within the PTV without protrusion.

Flexible Geometry (彈性幾何設定):

Customizable sphere size (diameter) and center-to-center spacing.

Supports Cubic and Hexagonal (Staggered) packing patterns.

Interactive Visualization (互動式視覺化):

Built-in 2D slice viewer with correct aspect ratio rendering.

Layer control to toggle visibility of PTV, Lattice, and OARs.

User-Friendly GUI (友善使用者介面):

No coding knowledge required. Built with tkinter for native Windows look and feel.

🛠️ Requirements & Installation (安裝與需求)
1. Clone the repository:

Bash

git clone https://github.com/YourUsername/Lattice-RT-System.git
cd Lattice-RT-System
2. Install dependencies:

Bash

pip install -r requirements.txt
3. Run the application:

Bash

python main.py
🚀 How to Use (使用說明)
File Loading:

Select the CT Folder containing the DICOM series.

Select the existing RT Structure File (.dcm).

Structure Selection:

Choose the Target PTV from the dropdown menu.

(Optional) Select one or multiple OARs to avoid (Hold Ctrl to select multiple).

Parameters:

Set Sphere Size (mm) and Spacing (mm).

Set Margin (mm) to define the buffer zone from PTV boundary.

Choose Packing Type: Cubic (Standard) or Hexagonal (Interlaced).

Generate:

Click "Generate". The system will process the masks and save a new DICOM RT Structure file.

A visualization window will pop up for verification.

⚠️ Disclaimer (免責聲明)
English: This software is for research and educational purposes only. It has not been cleared by the FDA or other regulatory bodies for clinical use. The user assumes all responsibility for verifying the accuracy of the generated structures before using them in a clinical setting.

中文: 本軟體僅供研究與教育用途。尚未經 FDA 或衛福部核准用於臨床醫療行為。使用者須自行承擔風險，並務必在臨床使用前，由合格醫學物理師或醫師驗證生成的結構準確性。
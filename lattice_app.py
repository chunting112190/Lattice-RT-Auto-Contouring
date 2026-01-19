import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pydicom
import pydicom.uid # 新增這個 import 用來生成全新 ID
import numpy as np
from rt_utils import RTStructBuilder
from scipy import ndimage

# Matplotlib 整合庫
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

# ==========================================
# 核心邏輯層 (Backend Logic)
# ==========================================
class LatticeCore:
    def __init__(self, log_callback):
        self.log = log_callback 

    def get_roi_names(self, rt_struct_path):
        try:
            ds = pydicom.dcmread(rt_struct_path, force=True)
            roi_names = []
            if 'StructureSetROISequence' in ds:
                for roi in ds.StructureSetROISequence:
                    roi_names.append(roi.ROIName)
            return sorted(roi_names)
        except Exception as e:
            self.log(f"讀取 ROI 失敗: {e}")
            return []

    def generate_and_get_data(self, params):
        try:
            self.log("Step 1/6: 載入 DICOM...")
            rtstruct = RTStructBuilder.create_from(
                dicom_series_path=params['ct_path'], 
                rt_struct_path=params['rt_path']
            )
            
            series_data = rtstruct.series_data 
            ct_volume = np.stack([s.pixel_array for s in series_data])
            
            first_dcm = series_data[0]
            pixel_spacing_y = float(first_dcm.PixelSpacing[0])
            pixel_spacing_x = float(first_dcm.PixelSpacing[1])
            view_aspect_ratio = pixel_spacing_y / pixel_spacing_x

            if len(series_data) > 1:
                slice_thickness = abs(series_data[0].ImagePositionPatient[2] - series_data[1].ImagePositionPatient[2])
            else:
                slice_thickness = first_dcm.SliceThickness or 1.0
            if slice_thickness == 0: slice_thickness = 1.0

            spacing_voxel = [
                params['spacing_mm'] / pixel_spacing_x,
                params['spacing_mm'] / pixel_spacing_y,
                params['spacing_mm'] / slice_thickness
            ]
            
            radius_mm = params['size_mm'] / 2.0
            radius_voxel_x = radius_mm / pixel_spacing_x
            radius_voxel_y = radius_mm / pixel_spacing_y
            radius_voxel_z = radius_mm / slice_thickness

            # --- Mask 處理 ---
            self.log("Step 2/6: 處理 Masks...")
            
            visualization_masks = {}

            def get_aligned_mask(roi_name):
                mask = rtstruct.get_roi_mask_by_name(roi_name)
                return np.transpose(mask, (2, 0, 1))

            try:
                ptv_mask = get_aligned_mask(params['ptv_name'])
                visualization_masks[params['ptv_name']] = {'data': ptv_mask, 'color': 'blue'} 
            except ValueError:
                raise ValueError(f"找不到 PTV: {params['ptv_name']}")
            
            base_mask = ptv_mask.copy()

            if params['oar_names']:
                colors = ['cyan', 'lime', 'magenta', 'orange', 'yellow', 'pink'] 
                for i, oar in enumerate(params['oar_names']):
                    try:
                        oar_mask = get_aligned_mask(oar)
                        visualization_masks[oar] = {'data': oar_mask, 'color': colors[i % len(colors)]}
                        base_mask = np.logical_and(base_mask, np.logical_not(oar_mask))
                    except:
                        pass

            # --- Step 3: Margin 計算 ---
            effective_margin_threshold = radius_mm + params['margin_mm']
            self.log(f"Step 3/6: 計算內縮範圍...")
            
            dist_map = ndimage.distance_transform_edt(
                base_mask, 
                sampling=[slice_thickness, pixel_spacing_y, pixel_spacing_x]
            )
            valid_placement_mask = dist_map >= effective_margin_threshold

            # --- Step 4: Lattice 生成 ---
            self.log(f"Step 4/6: 生成 Lattice 球體...")
            lattice_mask = np.zeros_like(base_mask, dtype=bool)
            
            z_idx, y_idx, x_idx = np.where(valid_placement_mask)
            
            if len(z_idx) == 0: 
                raise ValueError("空間不足，無法生成 Lattice。")
            
            z_min, z_max = np.min(z_idx), np.max(z_idx)
            y_min, y_max = np.min(y_idx), np.max(y_idx)
            x_min, x_max = np.min(x_idx), np.max(x_idx)

            z_grid = np.arange(z_min, z_max, spacing_voxel[2])
            count = 0
            
            for i, z in enumerate(z_grid):
                cz = int(z)
                if cz >= valid_placement_mask.shape[0]: continue

                offset_y, offset_x = 0.0, 0.0
                if params['packing_type'] == "交錯 (Hexagonal)" and (i % 2 == 1):
                    offset_y = spacing_voxel[1] / 2.0
                    offset_x = spacing_voxel[0] / 2.0
                
                current_y_grid = np.arange(y_min + offset_y, y_max, spacing_voxel[1])
                current_x_grid = np.arange(x_min + offset_x, x_max, spacing_voxel[0])

                for y in current_y_grid:
                    for x in current_x_grid:
                        cy, cx = int(y), int(x)
                        if (0 <= cy < valid_placement_mask.shape[1] and 0 <= cx < valid_placement_mask.shape[2]):
                            if valid_placement_mask[cz, cy, cx]:
                                self._draw_sphere(
                                    lattice_mask, 
                                    (cz, cy, cx), 
                                    (radius_voxel_z, radius_voxel_y, radius_voxel_x)
                                )
                                count += 1
            
            # --- Mask 轉置回 (y, x, z) 供 rt_utils 使用 ---
            lattice_mask_for_save = np.transpose(lattice_mask, (1, 2, 0))
            visualization_masks[params['out_name']] = {'data': lattice_mask, 'color': 'red'}

            self.log("Step 5/6: 轉換輪廓資料...")
            rtstruct.add_roi(
                mask=lattice_mask_for_save, 
                color=[255, 0, 0], 
                name=params['out_name']
            )
            
            # --- 【關鍵修復步驟】 ---
            self.log("Step 6/6: 強制更新 UID 並修復輪廓數據...")
            
            # 1. 解決 "Object Already Exists" -> 生成全新 UID
            self._regenerate_uids(rtstruct.ds)
            
            # 2. 解決 "Less than 3 points" & "VR DS" -> 過濾並格式化
            self._post_process_dicom(rtstruct.ds)

            rtstruct.save(params['out_path'])
            
            self.log(f"完成! 共生成 {count} 顆球體")
            return True, ct_volume, visualization_masks, view_aspect_ratio

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.log(f"錯誤: {str(e)}")
            return False, None, None, 1.0

    def _draw_sphere(self, mask_array, center, radii):
        cz, cy, cx = center
        rz, ry, rx = radii 
        z_min = max(0, int(cz - rz))
        z_max = min(mask_array.shape[0], int(cz + rz + 1))
        y_min = max(0, int(cy - ry))
        y_max = min(mask_array.shape[1], int(cy + ry + 1))
        x_min = max(0, int(cx - rx))
        x_max = min(mask_array.shape[2], int(cx + rx + 1))
        
        lz, ly, lx = np.ogrid[z_min:z_max, y_min:y_max, x_min:x_max]
        mask_slice = (
            ((lz - cz)**2) / (rz**2) + 
            ((ly - cy)**2) / (ry**2) + 
            ((lx - cx)**2) / (rx**2)
        ) <= 1
        mask_array[z_min:z_max, y_min:y_max, x_min:x_max] |= mask_slice

    def _regenerate_uids(self, dataset):
        """
        強制生成新的 SOP Instance UID 和 Series Instance UID。
        這能解決 Eclipse 報錯 'Connection not done: Object already exists'。
        """
        # 生成新的 SOP Instance UID
        new_sop_uid = pydicom.uid.generate_uid()
        dataset.SOPInstanceUID = new_sop_uid
        dataset.file_meta.MediaStorageSOPInstanceUID = new_sop_uid
        
        # 生成新的 Series Instance UID (讓 Eclipse 認為這是新的一組結構)
        dataset.SeriesInstanceUID = pydicom.uid.generate_uid()
        
        self.log("   -> 已生成全新 UID (SOP & Series)，避免重複錯誤")

    def _post_process_dicom(self, dataset):
        """
        強制檢查並修正所有輪廓數據：
        1. 刪除點數 < 3 的輪廓。
        2. 將所有座標強制轉為 4 位小數的字串，解決 VR DS 過長問題。
        """
        if 'ROIContourSequence' not in dataset:
            return

        total_cleaned = 0
        total_removed = 0

        for roi_contour in dataset.ROIContourSequence:
            if 'ContourSequence' not in roi_contour:
                continue
            
            valid_contours = []
            
            for contour in roi_contour.ContourSequence:
                # ContourData 是 [x1, y1, z1, x2, y2, z2...]，所以點數 = 長度 / 3
                num_points = len(contour.ContourData) // 3
                
                # 【嚴格過濾】 少於 3 點的直接丟棄
                if num_points < 3:
                    total_removed += 1
                    continue 
                
                # 【格式修正】 強制轉為字串
                try:
                    fixed_data = [f"{float(x):.4f}" for x in contour.ContourData]
                    contour.ContourData = fixed_data
                    contour.NumberOfContourPoints = num_points
                    valid_contours.append(contour)
                    total_cleaned += 1
                except:
                    valid_contours.append(contour)

            # 更新該 ROI 的輪廓序列
            roi_contour.ContourSequence = valid_contours

        self.log(f"   -> 已移除 {total_removed} 條無效輪廓 (點數不足)")
        self.log(f"   -> 已格式化 {total_cleaned} 條輪廓座標")

# ==========================================
# 視覺化視窗 (保持不變，複製即可)
# ==========================================
class VisualizerWindow(tk.Toplevel):
    def __init__(self, master, ct_volume, masks_dict, aspect_ratio):
        super().__init__(master)
        self.title("Lattice 結果檢視")
        self.geometry("1100x750")
        self.ct_volume = ct_volume
        self.masks_dict = masks_dict
        self.aspect_ratio = aspect_ratio
        self.total_slices = ct_volume.shape[0]
        self.current_slice = self.total_slices // 2
        self.mask_vars = {} 
        self._init_layout()
        self._plot_slice()

    def _init_layout(self):
        main_paned = ttk.PanedWindow(self, orient="horizontal")
        main_paned.pack(fill="both", expand=True)
        plot_frame = ttk.Frame(main_paned)
        main_paned.add(plot_frame, weight=3)
        self.fig = Figure(figsize=(6, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('black')
        self.fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        toolbar = NavigationToolbar2Tk(self.canvas, plot_frame)
        toolbar.update()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        slider_frame = ttk.Frame(plot_frame, padding=5)
        slider_frame.pack(fill="x", side="bottom")
        ttk.Label(slider_frame, text="Slice Index:").pack(side="left")
        self.slice_scale = ttk.Scale(slider_frame, from_=0, to=self.total_slices - 1, orient="horizontal", command=self._on_slider_change)
        self.slice_scale.set(self.current_slice)
        self.slice_scale.pack(side="left", fill="x", expand=True, padx=10)
        self.slice_label = ttk.Label(slider_frame, text=f"{self.current_slice}/{self.total_slices-1}")
        self.slice_label.pack(side="left")
        control_frame = ttk.Frame(main_paned, padding=10)
        main_paned.add(control_frame, weight=1)
        ttk.Label(control_frame, text="結構顯示", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        scroll_frame = ttk.Frame(control_frame)
        scroll_frame.pack(fill="both", expand=True)
        canvas_scroll = tk.Canvas(scroll_frame)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas_scroll.yview)
        self.check_frame = ttk.Frame(canvas_scroll)
        self.check_frame.bind("<Configure>", lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all")))
        canvas_scroll.create_window((0, 0), window=self.check_frame, anchor="nw")
        canvas_scroll.configure(yscrollcommand=scrollbar.set)
        canvas_scroll.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        for name, info in self.masks_dict.items():
            var = tk.BooleanVar(value=True)
            self.mask_vars[name] = var
            color_lbl = tk.Label(self.check_frame, text="  ", bg=info['color'], width=2)
            color_lbl.grid(sticky="w", padx=2, pady=2)
            chk = ttk.Checkbutton(self.check_frame, text=name, variable=var, command=self._plot_slice)
            row = self.check_frame.grid_size()[1]
            color_lbl.grid(row=row, column=0, sticky="w")
            chk.grid(row=row, column=1, sticky="w", padx=5)

    def _on_slider_change(self, value):
        idx = int(float(value))
        if idx != self.current_slice:
            self.current_slice = idx
            self.slice_label.config(text=f"{idx}/{self.total_slices-1}")
            self._plot_slice()

    def _plot_slice(self):
        self.ax.clear()
        ct_img = self.ct_volume[self.current_slice]
        self.ax.imshow(ct_img, cmap='gray', aspect=self.aspect_ratio)
        for name, var in self.mask_vars.items():
            if var.get():
                mask_3d = self.masks_dict[name]['data']
                mask_slice = mask_3d[self.current_slice]
                if np.max(mask_slice) > 0:
                    color = self.masks_dict[name]['color']
                    self.ax.contour(mask_slice.astype(float), levels=[0.5], colors=[color], linewidths=1.5, linestyles='solid', alpha=1.0)
        self.ax.set_title(f"Axial Slice: {self.current_slice}")
        self.ax.axis('off')
        self.canvas.draw()

# ==========================================
# 主應用程式 (GUI Main)
# ==========================================
class LatticeFinalApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lattice RT Pro (Ultimate Fix)")
        self.geometry("750x700")
        style = ttk.Style()
        style.theme_use('clam')
        self.ct_path_var = tk.StringVar()
        self.rt_path_var = tk.StringVar()
        self.output_name_var = tk.StringVar(value="Lattice_GTV")
        self.packing_var = tk.StringVar(value="標準 (Cubic)")
        self.core = LatticeCore(self.log_message)
        self._create_widgets()

    def _create_widgets(self):
        file_frame = ttk.LabelFrame(self, text="1. 檔案載入", padding=10)
        file_frame.pack(fill="x", padx=10, pady=5)
        f1 = ttk.Frame(file_frame); f1.pack(fill="x")
        ttk.Label(f1, text="CT 資料夾:").pack(side="left")
        ttk.Entry(f1, textvariable=self.ct_path_var).pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(f1, text="瀏覽", command=self.browse_ct).pack(side="left")
        f2 = ttk.Frame(file_frame); f2.pack(fill="x", pady=(5,0))
        ttk.Label(f2, text="RT 檔案:  ").pack(side="left")
        ttk.Entry(f2, textvariable=self.rt_path_var).pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(f2, text="瀏覽", command=self.browse_rt).pack(side="left")
        struct_frame = ttk.LabelFrame(self, text="2. 結構選擇", padding=10)
        struct_frame.pack(fill="both", expand=True, padx=10, pady=5)
        left_panel = ttk.Frame(struct_frame)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        ttk.Label(left_panel, text="目標 PTV:").pack(anchor="w")
        self.ptv_combo = ttk.Combobox(left_panel, state="readonly", width=25)
        self.ptv_combo.pack(fill="x", pady=5)
        ttk.Button(left_panel, text="讀取列表", command=self.load_roi_list).pack(fill="x", pady=5)
        right_panel = ttk.Frame(struct_frame)
        right_panel.pack(side="left", fill="both", expand=True)
        ttk.Label(right_panel, text="避開的 OAR (Ctrl 多選):", font=("Arial", 9, "bold")).pack(anchor="w")
        list_scroll_frame = ttk.Frame(right_panel)
        list_scroll_frame.pack(fill="both", expand=True, pady=2)
        scrollbar = ttk.Scrollbar(list_scroll_frame, orient="vertical")
        self.oar_listbox = tk.Listbox(list_scroll_frame, selectmode="extended", height=5, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.oar_listbox.yview)
        self.oar_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        param_frame = ttk.LabelFrame(self, text="3. 參數設定", padding=10)
        param_frame.pack(fill="x", padx=10)
        ttk.Label(param_frame, text="Size(mm):").grid(row=0, column=0, sticky="w")
        self.size_spin = ttk.Spinbox(param_frame, from_=1, to=50, width=5); self.size_spin.set(15.0)
        self.size_spin.grid(row=0, column=1, sticky="w", padx=5)
        ttk.Label(param_frame, text="Dist(mm):").grid(row=0, column=2, sticky="w", padx=10)
        self.dist_spin = ttk.Spinbox(param_frame, from_=1, to=100, width=5); self.dist_spin.set(60.0)
        self.dist_spin.grid(row=0, column=3, sticky="w", padx=5)
        ttk.Label(param_frame, text="Margin(mm):").grid(row=1, column=0, sticky="w", pady=5)
        self.margin_spin = ttk.Spinbox(param_frame, from_=0, to=30, width=5); self.margin_spin.set(7.5)
        self.margin_spin.grid(row=1, column=1, sticky="w", padx=5)
        ttk.Label(param_frame, text="Packing:").grid(row=1, column=2, sticky="w", padx=10)
        self.packing_combo = ttk.Combobox(param_frame, values=["標準 (Cubic)", "交錯 (Hexagonal)"], textvariable=self.packing_var, width=15, state="readonly")
        self.packing_combo.grid(row=1, column=3, sticky="w", padx=5)
        ttk.Label(param_frame, text="Output Name:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(param_frame, textvariable=self.output_name_var).grid(row=2, column=1, columnspan=3, sticky="ew", padx=5)
        self.run_btn = ttk.Button(self, text="開始生成 (Generate)", command=self.start_processing)
        self.run_btn.pack(fill="x", padx=20, pady=10)
        self.log_text = tk.Text(self, height=6)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def browse_ct(self):
        path = filedialog.askdirectory()
        if path: self.ct_path_var.set(path)
    def browse_rt(self):
        path = filedialog.askopenfilename(filetypes=[("DICOM", "*.dcm")])
        if path: 
            self.rt_path_var.set(path)
            self.load_roi_list()
    def load_roi_list(self):
        if not self.rt_path_var.get(): return
        threading.Thread(target=self._load_roi_thread, args=(self.rt_path_var.get(),), daemon=True).start()
    def _load_roi_thread(self, rt_path):
        names = self.core.get_roi_names(rt_path)
        self.after(0, lambda: self.ptv_combo.config(values=names))
        self.after(0, lambda: self.oar_listbox.delete(0, tk.END))
        for n in names: self.after(0, lambda n=n: self.oar_listbox.insert(tk.END, n), n)
    def log_message(self, msg):
        self.log_text.insert("end", msg+"\n")
        self.log_text.see("end")
    def start_processing(self):
        ptv = self.ptv_combo.get()
        idxs = self.oar_listbox.curselection()
        oars = [self.oar_listbox.get(i) for i in idxs]
        if ptv in oars: oars.remove(ptv)
        if not ptv or not self.ct_path_var.get() or not self.rt_path_var.get():
            messagebox.showerror("錯誤", "請確認所有欄位設定")
            return
        try:
            params = {
                'ct_path': self.ct_path_var.get(),
                'rt_path': self.rt_path_var.get(),
                'ptv_name': ptv,
                'oar_names': oars,
                'size_mm': float(self.size_spin.get()),
                'spacing_mm': float(self.dist_spin.get()),
                'margin_mm': float(self.margin_spin.get()),
                'packing_type': self.packing_var.get(),
                'out_name': self.output_name_var.get(),
                'out_path': os.path.join(os.path.dirname(self.rt_path_var.get()), f"Lattice_{self.output_name_var.get()}.dcm")
            }
        except ValueError:
            return
        self.run_btn.config(state="disabled")
        threading.Thread(target=self._run_thread, args=(params,), daemon=True).start()
    def _run_thread(self, params):
        success, ct_vol, masks, aspect = self.core.generate_and_get_data(params)
        self.after(0, lambda: self.run_btn.config(state="normal"))
        if success:
            self.after(0, lambda: messagebox.showinfo("完成", "生成成功！檔案 ID 已更新。"))
            self.after(0, lambda: VisualizerWindow(self, ct_vol, masks, aspect))

if __name__ == "__main__":
    app = LatticeFinalApp()
    app.mainloop()
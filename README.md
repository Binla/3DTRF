# 3DTRF (3D Mesh to Solid/STEP Converter)

自動針對 Fusion 360 等 CAD 軟體設計的 3D 幾何與 Mesh (STL/OBJ) 模型轉檔與最佳化工貝。

## 安裝與執行方式

### 方法一：使用現成執行檔 (最簡單，推薦一般使用者)

1. 到本專案的 [Releases](https://github.com/Binla/3DTRF/releases) 頁面 (請開發者在此上傳打包好的 `3DTRF.exe` 或是包含 `dist/3DTRF` 的壓縮檔)。
2. 下載並解壓縮檔案。
3. 雙擊執行 `3DTRF.exe` 即可開啟程式。

### 方法二：下載原始碼自行執行 (適合開發者)

如果您有安裝 Python環境，可以下載原始碼直接執行。

1. **安裝 Python**
   請確保您的電腦已安裝 Python 3.10 或以上版本。

2. **下載本專案**
   在您的終端機輸入：
   ```cmd
   git clone https://github.com/Binla/3DTRF.git
   cd 3DTRF
   ```
   *(或者您也可以直接在 GitHub 點擊 `Code` -> `Download ZIP` 並解壓縮)*

3. **執行啟動腳本**
   直接對 `start_3DTRF.bat` 點擊兩下執行。
   這個腳本會自動檢查並安裝所需的套件 (例如 Flet, trimesh, numpy 等)，接著啟動應用程式。

4. *(選擇性)* **使用 STEP 引擎**
   為了確保 STEP 轉檔功能 (`Aspose.CAD`) 可正確運作：
   程式預設會在 `deps/python310/python.exe` 尋找可用的 Python 執行環境。如果您是在自己的開發環境下運行，請確保您的全域 / 虛擬環境也透過 `pip install -r requirements.txt` 以及 `pip install aspose-cad` 完成安裝。

## 自行打包成執行檔

如果您希望自己建置 `3DTRF.exe`：

1. 確認已安裝好所有依賴。
2. 點擊執行 `build_exe.bat`。
3. 等待 PyInstaller 處理完成後，您即可在專案出現的 `dist/3DTRF/` 資料夾中找到打包好的 `3DTRF.exe` 檔案與需要的檔案。

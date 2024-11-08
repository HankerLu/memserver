from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from PIL import Image
import io
import json
import os
from typing import List
from pydantic import BaseModel
from TestFuncs import analyzer

app = FastAPI()

# 配置静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PoemRequest(BaseModel):
    keywords: List[str]
    poem_type: str

@app.on_event("startup")
async def startup_event():
    """服务启动时初始化模型"""
    if not analyzer.initialize():
        raise RuntimeError("模型初始化失败")

@app.post("/analyze_image")
async def analyze_image(file: UploadFile):
    """图像分析接口"""
    try:
        # 读取上传的图片
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # 分析图片
        description, keywords = analyzer.analyze_image(image)
        
        # 解析关键词字符串为列表
        try:
            keywords_list = json.loads(keywords.replace("'", '"'))
        except:
            # 同时处理中英文逗号分隔
            keywords_list = keywords.strip('[]').replace('，', ',').split(',')
            keywords_list = [k.strip() for k in keywords_list]
        
        return {
            "status": "success",
            "description": description,
            "keywords": keywords_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create_poem")
async def create_poem(request: PoemRequest):
    """创建诗歌接口"""
    try:
        poem = analyzer.create_poem(request.keywords, request.poem_type)
        return {
            "status": "success",
            "poem": poem
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}

@app.get("/api/images")
async def get_images():
    """返回static文件夹下的所有PNG图片"""
    print("Received request for PNG images")
    static_dir = "static"
    
    # 确保static目录存在
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        print(f"Created static directory at path: {static_dir}")
    
    # 获取所有PNG文件
    png_files = []
    for file in os.listdir(static_dir):
        if file.lower().endswith('.png'):
            file_path = os.path.join(static_dir, file)
            png_files.append({
                "filename": file,
                "url": f"/static/{file}"
            })
    
    print(f"Found {len(png_files)} PNG files")
    return {"images": png_files}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 
# 使用 Node.js 20 映像
FROM node:20-alpine

# 設置工作目錄
WORKDIR /app

# 複製 package.json 和 package-lock.json
COPY package*.json ./

# 不在這裡安裝依賴，等待容器啟動時處理

# 複製源代碼
COPY . .
RUN chmod -R 755 /app && find /app -type f -exec chmod 644 {} \;

# 暴露端口
EXPOSE 3000

# 開發環境會延遲到容器啟動時才執行
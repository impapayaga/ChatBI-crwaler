# 构建阶段：使用Node.js构建前端
FROM node:18-alpine AS build

WORKDIR /app

# 安装pnpm并配置国内镜像源
RUN npm install -g pnpm && \
    pnpm config set registry https://registry.npmmirror.com

# 复制package文件
COPY package.json pnpm-lock.yaml ./

# 安装依赖
RUN pnpm install

# 复制源代码
COPY . .

# 构建生产版本（注意：先用localhost，后续有服务器地址后需要重新构建）
ARG VITE_API_BASE_URL=http://localhost:11434
# VITE_CRAWLER_API_BASE_URL 已禁用（生产环境不使用爬虫功能）
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# 构建（跳过类型检查，直接使用 vite build）
RUN echo "Building with VITE_API_BASE_URL=$VITE_API_BASE_URL" && \
    npx vite build

# 生产阶段：使用Nginx提供静态文件
FROM nginx:alpine

# 复制构建结果到nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Nginx配置
RUN echo 'server { \
    listen 80; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ { \
        expires 1y; \
        add_header Cache-Control "public, immutable"; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]


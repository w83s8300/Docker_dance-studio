# 使用 PHP 基礎映像檔
FROM php:8.2-fpm

# 安裝相關依賴套件
RUN apt-get update > /dev/null && apt-get install -y \
   git \
   unzip \
   libjpeg-dev \
   libxpm-dev \
   libwebp-dev \
   libfreetype6-dev \
   libjpeg62-turbo-dev \
   libzip-dev \
   libpng-dev \
   zlib1g-dev \
   libicu-dev \
   jpegoptim \
   g++ \
   libxrender1 \
   libfontconfig

# 安裝 PHP zip 擴展
RUN docker-php-ext-install intl > /dev/null \
   && docker-php-ext-install zip > /dev/null \
   && docker-php-ext-install bcmath > /dev/null \
   && docker-php-ext-install pdo pdo_mysql mysqli > /dev/null

# 安裝 Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# 設置工作目錄
WORKDIR /var/www/html

# 複製專案檔案
COPY ../../api .

# 設置正確的權限
RUN mkdir -p /var/www/storage \
    && chown -R www-data:www-data /var/www \
    && chmod -R 755 /var/www/storage
# Expose port 9000 and start PHP-FPM server
EXPOSE 9000
CMD ["php-fpm"]
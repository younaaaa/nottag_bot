#!/bin/bash

echo "در حال ایجاد نسخه پشتیبان از پایگاه داده..."

docker exec bot_postgres pg_dump -U bot_admin bot_database > backup.sql

echo "پشتیبان‌گیری با موفقیت انجام شد!"
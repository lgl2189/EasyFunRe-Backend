package com.star.easyfun.content.service;

import com.star.easyfun.content.config.property.MinioProperty;
import io.minio.*;
import io.minio.http.Method;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.InputStream;
import java.util.UUID;

/**
 * @author ：Star
 * @description ：无描述
 * @date ：2026 3月 26 18:09
 */


@Service
@RequiredArgsConstructor
public class MinioService {

    private final MinioClient minioClient;
    private final MinioProperty minioProperty;

    private static final Logger logger = LogManager.getLogger(MinioService.class);

    // 1. 上传文件（返回预签名下载URL）
    public String upload(MultipartFile file, String folder) throws Exception {
        String objectName = folder + "/"
                + UUID.randomUUID()
                + "_" + file.getOriginalFilename();

        minioClient.putObject(
                PutObjectArgs.builder()
                        .bucket(minioProperty.getBucket())
                        .object(objectName)
                        .stream(file.getInputStream(), file.getSize(), -1)
                        .contentType(file.getContentType())
                        .build()
        );

        return getPresignedGetUrl(objectName, minioProperty.getExpirySeconds());
    }

    // 2. 获取预签名下载URL（前端直接访问，推荐）
    public String getPresignedGetUrl(String objectName, int expirySeconds) throws Exception {
        return minioClient.getPresignedObjectUrl(
                GetPresignedObjectUrlArgs.builder()
                        .method(Method.GET)
                        .bucket(minioProperty.getBucket())
                        .object(objectName)
                        .expiry(expirySeconds)
                        .build()
        );
    }

    // 3. 获取预签名上传URL（前端可直接 PUT 上传，适合大文件）
    public String getPresignedPutUrl(String objectName, int expirySeconds) throws Exception {
        return minioClient.getPresignedObjectUrl(
                GetPresignedObjectUrlArgs.builder()
                        .method(Method.PUT)
                        .bucket(minioProperty.getBucket())
                        .object(objectName)
                        .expiry(expirySeconds)
                        .build()
        );
    }

    // 4. 下载文件流（后端使用）
    public InputStream download(String objectName) throws Exception {
        return minioClient.getObject(
                GetObjectArgs.builder()
                        .bucket(minioProperty.getBucket())
                        .object(objectName)
                        .build()
        );
    }

    // 5. 删除文件
    public void delete(String objectName) throws Exception {
        minioClient.removeObject(
                RemoveObjectArgs.builder()
                        .bucket(minioProperty.getBucket())
                        .object(objectName)
                        .build()
        );
    }

    // 6. 检查并创建桶（启动时调用一次）
    public void ensureBucketExists() throws Exception {
        boolean exists = minioClient.bucketExists(
                BucketExistsArgs.builder().bucket(minioProperty.getBucket()).build()
        );
        if (!exists) {
            minioClient.makeBucket(
                    MakeBucketArgs.builder().bucket(minioProperty.getBucket()).build()
            );
        }
    }

    @PostConstruct
    public void init() {
        try {
            ensureBucketExists();
            logger.info("MinIO 默认桶已就绪: {}", minioProperty.getBucket());
        } catch (Exception e) {
            logger.error("MinIO 桶初始化失败: {}", e.getMessage());
        }
    }
}
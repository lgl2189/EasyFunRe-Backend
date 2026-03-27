package com.star.easyfun.content.controller;

import com.star.easyfun.content.service.MinioService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

/**
 * @author ：Star
 * @description ：无描述
 * @date ：2026 3月 26 18:11
 */

@RestController
@RequiredArgsConstructor
public class FileController {
    private final MinioService minioService;
    @PostMapping("/upload")
    public String uploadFile(@RequestParam("file") MultipartFile file) throws Exception {
        return minioService.upload(file, "uploads/images");
    }
}
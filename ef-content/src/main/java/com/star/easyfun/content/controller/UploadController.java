package com.star.easyfun.content.controller;

import com.star.easyfun.common.constant.CommonRequestHeader;
import com.star.easyfun.common.pojo.dto.Result;
import com.star.easyfun.common.util.ResultUtil;
import com.star.easyfun.content.pojo.dto.VideoPostDTO;
import com.star.easyfun.content.service.ContentService;
import com.star.easyfun.content.service.MinioService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * @author ：Star
 * @description ：无描述
 * @date ：2026 3月 26 18:11
 */

@RestController
@RequestMapping("/upload")
@RequiredArgsConstructor
public class UploadController {
    private final ContentService contentService;

    @PostMapping(value = "/post/video")
    public Result uploadPost(VideoPostDTO videoPostDTO,@RequestHeader(CommonRequestHeader.HEADER_USER_ID) Long userId) {
        // 调用业务层发布投稿
        contentService.uploadVideoPost(videoPostDTO,userId);
        return ResultUtil.success_10000(null, "视频投稿发布成功");
    }
}
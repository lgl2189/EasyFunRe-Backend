package com.star.easyfun.content.controller;

import com.star.easyfun.common.constant.CommonRequestHeader;
import com.star.easyfun.common.pojo.dto.Result;
import com.star.easyfun.common.util.ResultUtil;
import com.star.easyfun.content.pojo.dto.VideoPostDTO;
import com.star.easyfun.content.service.ContentService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * @author ：Star
 * @description ：所有与投稿有关的接口
 * @date ：2026 3月 26 18:11
 */

@RestController
@RequestMapping("/post")
@RequiredArgsConstructor
public class PostController {
    private final ContentService contentService;

    @PostMapping("/video")
    public Result uploadPost(VideoPostDTO videoPostDTO, @RequestHeader(CommonRequestHeader.HEADER_USER_ID) Long userId) {
        // 调用业务层发布投稿
        contentService.uploadVideoPost(videoPostDTO, userId);
        return ResultUtil.success_10000(null, "视频投稿发布成功");
    }

    // 不写路径默认为（""），如果写为 "/"，则表示路径末尾必须带 斜杠/，即/content/post/，不带斜杠无法匹配到该接口
    @GetMapping
    public Result getPost(@RequestParam("resourceId") Long resourceId) throws Exception {
        // TODO: 这个接口根据资源id
        String playUrl = contentService.getVideoPlayUrl(resourceId);
        return ResultUtil.success_10000(playUrl, "测试视频投稿");
    }
}
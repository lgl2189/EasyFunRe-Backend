package com.star.easyfun.content.controller;

import com.star.easyfun.common.constant.CommonRequestHeader;
import com.star.easyfun.common.pojo.dto.Result;
import com.star.easyfun.common.util.ResultUtil;
import com.star.easyfun.content.pojo.dto.ContentPostDTO;
import com.star.easyfun.content.pojo.dto.VideoPostUploadDTO;
import com.star.easyfun.content.service.BehaviorRecordAsyncService;
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
    private final BehaviorRecordAsyncService behaviorRecordAsyncService;

    @PostMapping("/video")
    public Result uploadPost(VideoPostUploadDTO videoPostUploadDTO, @RequestHeader(CommonRequestHeader.HEADER_USER_ID) Long userId) {
        // 调用业务层发布投稿
        contentService.uploadVideoPost(videoPostUploadDTO, userId);
        return ResultUtil.success_10000(null, "视频投稿发布成功");
    }

    // 不写路径默认为（""），如果写为 "/"，则表示路径末尾必须带 斜杠/，即/content/post/，不带斜杠无法匹配到该接口
    // 不能删除@PathVariable注解的"postId"参数，高版本SpringBoot未开启-parameter时，无法获取参数名，导致路径无法匹配，最终找不到匹配的接口
    @GetMapping("/{postId}")
    public Result getPost(@PathVariable("postId") Long postId,
                          @RequestHeader(CommonRequestHeader.HEADER_USER_ID) Long userId
    ) throws Exception {
        // TODO: 这个接口根据资源id
        ContentPostDTO contentPostDTO = contentService.getPost(postId);
        contentService.recordBrowsePost(postId, userId);
        return ResultUtil.success_10000(contentPostDTO, "测试视频投稿");
    }

    @PostMapping("/{postId}/like")
    public Result likePost(@PathVariable("postId") Long postId,
                           @RequestHeader(CommonRequestHeader.HEADER_USER_ID) Long userId,
                           @RequestParam("isLike") Boolean isLike) {
        boolean isSuccess = contentService.updatePostLike(postId, userId, isLike);
        if (!isSuccess) {
            if (isLike) {
                return ResultUtil.fail_20000("点赞失败，当前已为点赞状态");
            }
            return ResultUtil.fail_20000("取消点赞失败，当前已为未点赞状态");
        }
        return ResultUtil.success_10000(null, "点赞成功");
    }
}
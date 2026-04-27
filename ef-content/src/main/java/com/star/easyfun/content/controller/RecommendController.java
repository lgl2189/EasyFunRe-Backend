package com.star.easyfun.content.controller;

import com.star.easyfun.common.constant.CommonRequestHeader;
import com.star.easyfun.common.pojo.dto.Result;
import com.star.easyfun.common.util.ResultUtil;
import com.star.easyfun.content.pojo.dbo.ContentInteractionRecordDBO;
import com.star.easyfun.content.pojo.dbo.ContentPostDBO;
import com.star.easyfun.content.pojo.dto.ContentPostDTO;
import com.star.easyfun.content.pojo.dto.recommend.RecommendTagDTO;
import com.star.easyfun.content.service.RecommendService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * @author ：Star
 * @description ：无描述
 * @date ：2026 4月 19 13:13
 */
@RestController
@RequestMapping("/recommend")
@RequiredArgsConstructor
public class RecommendController {
    private final RecommendService recommendService;

    @GetMapping("/list")
    public Result recommendPostList(
            @RequestHeader(CommonRequestHeader.HEADER_USER_ID) Long userId,
            @RequestParam("pageSize") Integer pageSize,
            @RequestParam("alpha") Float alpha,
            @RequestParam("wDiv") Float wDiv,
            @RequestParam("wBound") Float wBound) {
        List<ContentPostDTO> contentPostDTOList = recommendService.getRecommendPostList(userId, pageSize, alpha, wDiv, wBound);
        return ResultUtil.success_10000(contentPostDTOList, "推荐列表获得成功");
    }

    @GetMapping("/video/all")
    public Result getAllVideo() {
        List<ContentPostDBO> postList = recommendService.getAllPost();
        return ResultUtil.success_10000(postList, "推荐视频列表获得成功");
    }

    @GetMapping("/interaction/all")
    public Result getAllInteractionRecord() {
        List<ContentInteractionRecordDBO> interactionList = recommendService.getAllInteractionRecord();
        return ResultUtil.success_10000(interactionList, "推荐互动记录列表获得成功");
    }

    @GetMapping("/tag/list")
    public Result getTagList() {
        List<RecommendTagDTO> tagList = recommendService.getTagList();
        return ResultUtil.success_10000(tagList, "标签列表获得成功");
    }

}
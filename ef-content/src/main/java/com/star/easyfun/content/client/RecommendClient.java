package com.star.easyfun.content.client;

import com.star.easyfun.content.pojo.dto.recommend.RecommendPostListDTO;
import com.star.easyfun.content.pojo.dto.recommend.RecommendRequestDTO;
import com.star.easyfun.content.pojo.dto.recommend.RecommendTagDTO;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;

import java.util.List;

/**
 * @author ：Star
 * @description ：无描述
 * @date ：2026 4月 19 13:57
 */
@FeignClient(
        name = "recommend-service",
        url = "http://localhost:8095"
)
public interface RecommendClient {
    /**
     * 获取推荐投稿列表
     */
    @PostMapping("/recommend/list")
    RecommendPostListDTO getRecommendPostList(@RequestParam("userId") Long userId,
                                              @RequestParam("isColdStart") Boolean isColdStart,
                                              @RequestParam("pageSize") Integer pageSize,
                                              @RequestParam("alpha") Float alpha,
                                              @RequestParam("wDiv") Float wDiv,
                                              @RequestParam("wBound") Float wBound,
                                              @RequestBody RecommendRequestDTO recommendRequestDTO);

    /**
     * 获取冷启动标签列表
     * @param limit 获取的标签数量。必须大于等于10
     * @return 冷启动标签列表
     */
    @GetMapping("/recommend/cold-start/tags")
    List<RecommendTagDTO> getColdStartTagList(@RequestParam("limit") Integer limit);

}
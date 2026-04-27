package com.star.easyfun.content.pojo.dto.recommend;

import com.star.easyfun.content.pojo.dbo.ContentInteractionRecordDBO;
import com.star.easyfun.content.pojo.dbo.ContentPostDBO;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

import java.util.List;

/**
 * @author ：Star
 * @description ：无描述
 * @date ：2026 4月 19 20:26
 */

@Data
@NoArgsConstructor
@AllArgsConstructor
@Accessors(chain = true)
public class RecommendRequestDTO {
    List<ContentPostDBO> postList;
    List<ContentInteractionRecordDBO> interactionList;
}
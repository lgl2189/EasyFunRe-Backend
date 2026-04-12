package com.star.easyfun.content.pojo.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

import java.time.LocalDateTime;
import java.util.List;

/**
 * @author ：Star
 * @description ：存储一个投稿的所有信息
 * @date ：2026 4月 12 14:40
 */

@Data
@NoArgsConstructor
@AllArgsConstructor
@Accessors(chain = true)
public class ContentPostDTO {
    private Long postId;
    /**
     * 投稿者的用户ID
     */
    private Long ownerId;
    /**
     * 投稿标题
     */
    private String title;
    /**
     * 投稿描述/简介
     */
    private String description;
    /**
     * 投稿封面图云存储原始Key
     */
    private String coverKey;
    /**
     * 投稿封面图地址
     */
    private String coverUrl;
    /**
     * 投稿类型：1=普通投稿，2=合集
     */
    private Integer postType;
    /**
     * 可见性：1=公开，2=私密
     */
    private Integer isVisibility;
    /**
     * 是否允许评论：1=允许，0=关闭
     */
    private Integer allowComment;
    /**
     * 投稿状态：1=已发布，2=草稿，3=审核中，0=已删除
     */
    private Integer status;
    /**
     * 播放量/浏览量
     */
    private Integer viewCount;
    /**
     * 点赞量
     */
    private Integer likeCount;
    /**
     * 评论数量
     */
    private Integer commentCount;
    /**
     * 关联的评论区ID
     */
    private Long commentAreaId;
    /**
     * 创建时间
     */
    private LocalDateTime createdAt;
    /**
     * 实际发布时间（草稿转为发布时更新）
     */
    private LocalDateTime publishedAt;
    /**
     * 修改时间
     */
    private LocalDateTime updatedDatetime;
    /**
     * 投稿的资源列表
     */
    private List<ContentResourceDTO> resourceList;
}
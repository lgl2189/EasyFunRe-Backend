package com.star.easyfun.content.pojo.dbo;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

import java.io.Serial;
import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 投稿信息表 - 存储一个投稿本身的信息(content_post)实体类
 *
 * @author Star
 * @since 2026-04-08 21:08:39
 * @description 
 */
@Data
@NoArgsConstructor
@Accessors(chain = true)
@TableName("content_post")
public class ContentPost implements Serializable {
    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 投稿主键ID
     */
    @TableId
	private Long postId;
    /**
     * 投稿的用户ID
     */
    private Long ownerId;
    /**
     * 投稿标题（视频标题、作品标题等）
     */
    private String title;
    /**
     * 投稿描述/简介
     */
    private String description;
    /**
     * 投稿封面图地址
     */
    private String coverKey;
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

}
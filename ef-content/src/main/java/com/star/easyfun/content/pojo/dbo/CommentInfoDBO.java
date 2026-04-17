package com.star.easyfun.content.pojo.dbo;

import java.io.Serial;
import java.io.Serializable;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

/**
 * 评论表 - 存储一条评论的信息(comment_info)实体类
 *
 * @author Star
 * @since 2026-04-08 21:08:39
 * @description 
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Accessors(chain = true)
@TableName("comment_info")
public class CommentInfoDBO implements Serializable {
    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 评论的唯一标识，自增主键
     */
    @TableId
	private Long commentId;
    /**
     * 所属评论区ID
     */
    private Long commentAreaId;
    /**
     * 根评论ID（0表示自己就是root）
     */
    private Long rootId;
    /**
     * 父评论ID（0表示是root）
     */
    private Long parentId;
    /**
     * 评论层级：0 = Root，1 = 一级回复，2 = 二级回复（及以后所有回复）
     */
    private Integer level;
    /**
     * 发表该评论的用户ID
     */
    private Long userId;
    /**
     * 本评论回复给哪个用户（@某人），根评论则为投稿者本人的用户ID
     */
    private Long toUserId;
    /**
     * 评论内容
     */
    private String content;
    /**
     * 点赞数量
     */
    private Integer likeCount;
    /**
     * 子回复数量（建议仅对 level=0 和 level=1 维护）
     */
    private Integer replyCount;
    /**
     * 是否置顶（仅对0级Root评论有效）：0-未置顶，1-置顶
     */
    private Integer isTop;
    /**
     * 创建时间
     */
    private LocalDateTime createdAt;
    /**
     * 删除标记：0-正常，1-已删除
     */
    private Integer isDelete;

}
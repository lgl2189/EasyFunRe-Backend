package com.star.easyfun.content.pojo.dbo;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

import java.io.Serial;
import java.io.Serializable;

/**
 * 存储用户与投稿内容进行的互动记录(content_interaction_record)实体类
 *
 * @author Star
 * @since 2026-04-12 14:34:30
 * @description 
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Accessors(chain = true)
@TableName("content_interaction_record")
public class ContentInteractionRecordDBO implements Serializable {
    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 主键ID，自增
     */
    @TableId
	private Long interactionId;
    /**
     * 进行操作的用户的ID
     */
    private Long ownerId;
    /**
     * 被进行操作的投稿的ID
     */
    private Long targetPostId;
    /**
     * 用户是否进行点赞操作
     */
    private Integer isLike;

}
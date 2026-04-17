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
 * 评论区表 - 存储一个评论区的信息(comment_area)实体类
 *
 * @author Star
 * @since 2026-04-08 21:08:39
 * @description 
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Accessors(chain = true)
@TableName("comment_area")
public class CommentAreaDBO implements Serializable {
    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 评论区的唯一标识，自增主键
     */
    @TableId
	private Long commentAreaId;
    /**
     * 评论区总评论的数量
     */
    private Integer commentCount;
    /**
     * 评论区所有根评论的数量
     */
    private Integer rootCount;
    /**
     * 评论区的状态：1=正常，2=关闭
     */
    private Integer status;
    /**
     * 评论区的创建时间
     */
    private LocalDateTime createdAt;
    /**
     * 删除标记：0-正常，1-已删除
     */
    private Integer isDelete;

}
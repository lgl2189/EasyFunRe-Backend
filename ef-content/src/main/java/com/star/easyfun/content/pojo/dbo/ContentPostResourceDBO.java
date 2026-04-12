package com.star.easyfun.content.pojo.dbo;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

import java.io.Serial;
import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 投稿内容项表 - 存储一个投稿中有哪些内容的信息(content_post_resource)实体类
 *
 * @author Star
 * @since 2026-04-08 21:08:39
 * @description 
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Accessors(chain = true)
@TableName("content_post_resource")
public class ContentPostResourceDBO implements Serializable {
    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 投稿列表项的唯一标识，自增主键
     */
    @TableId
	private Long postResourceId;
    /**
     * 所属投稿ID
     */
    private Long postId;
    /**
     * 内容ID（关联 content_asset.asset_id）
     */
    private Long resourceId;
    /**
     * 排序序号（同一个投稿内内容的显示顺序，从小到大）
     */
    private Integer sortOrder;
    /**
     * 创建时间
     */
    private LocalDateTime createdDatetime;
    /**
     * 修改时间
     */
    private LocalDateTime updatedDatetime;

}
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
 * 推荐参数表(recommend_param)实体类
 *
 * @author Star
 * @since 2026-04-28 14:55:34
 * @description 
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Accessors(chain = true)
@TableName("recommend_param")
public class RecommendParamDBO implements Serializable {
    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 主键，自动增长
     */
    @TableId
	private Long paramId;
    /**
     * 用户id
     */
    private Long userId;
    /**
     * 融合比例，0-1
     */
    private Float alpha;
    /**
     * 多样性比例，0-1
     */
    private Float wDiv;
    /**
     * 破圈比例，0-1
     */
    private Float wBound;

}
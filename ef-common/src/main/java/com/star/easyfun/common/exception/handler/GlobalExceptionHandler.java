package com.star.easyfun.common.exception.handler;


import com.star.easyfun.common.pojo.dto.Result;
import com.star.easyfun.common.pojo.dto.ResultStatus;
import com.star.easyfun.common.util.ResultUtil;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import jakarta.validation.Payload;
import jakarta.validation.metadata.ConstraintDescriptor;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.Set;

/**
 * @author ：Star
 * @description ：无描述
 * @date ：2026 2月 24 18:22
 */


@RestControllerAdvice
public class GlobalExceptionHandler {
    private static final Logger logger = LogManager.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public Result handleValidationException(MethodArgumentNotValidException e) {
        FieldError fieldError = e.getBindingResult().getFieldError();
        if (fieldError == null) {
            return ResultUtil.fail_50000("出现系统内部错误，参数验证失败");
        }
        ConstraintDescriptor<?> descriptor = fieldError.unwrap(ConstraintViolation.class).getConstraintDescriptor();
        Set<Class<? extends Payload>> payloadSet = descriptor.getPayload();
        return payloadSet.isEmpty() ? ResultUtil.fail_50000("出现系统内部错误，参数验证失败") : handleStatus(payloadSet, fieldError.getDefaultMessage());
    }

    @ExceptionHandler(ConstraintViolationException.class)
    public Result handleConstraintViolationException(ConstraintViolationException e) {
        ConstraintDescriptor<?> descriptor = e.getConstraintViolations().stream()
                .findFirst()
                .map(ConstraintViolation::getConstraintDescriptor).orElse(null);
        if (descriptor == null) {
            return ResultUtil.fail_50000("出现系统内部错误，参数验证失败");
        }
        Set<Class<? extends Payload>> payloadSet = descriptor.getPayload();
        return payloadSet.isEmpty() ? ResultUtil.fail_50000("出现系统内部错误，参数验证失败") : handleStatus(payloadSet, e.getMessage());
    }

    private Result handleStatus(Set<Class<? extends Payload>> payloadSet, String message) {
        Class<? extends Payload> clazz = payloadSet.stream().findFirst().orElse(null);
        if (clazz == ResultStatus.Status20000.class) {
            return ResultUtil.fail_20000(message != null ? message : "参数验证失败");
        }
        else if (clazz == ResultStatus.Status20001.class) {
            return ResultUtil.fail_20001(message != null ? message : "缺少必填参数");
        }
        else if (clazz == ResultStatus.Status20002.class) {
            return ResultUtil.fail_20002(message != null ? message : "参数格式错误");
        }
        else if (clazz == ResultStatus.Status20003.class) {
            return ResultUtil.fail_20003(message != null ? message : "参数值超出范围");
        }
        else if (clazz == ResultStatus.Status20004.class) {
            return ResultUtil.fail_20004(message != null ? message : "重复提交");
        }
        return ResultUtil.fail_50000("出现系统内部错误，参数验证失败");
    }

    @ExceptionHandler(Exception.class)
    public Result handleException(Exception e) {
        // 1. 记录详细错误日志（最重要！）
        logger.error("系统发生未捕获异常", e);   // 这样会打印完整堆栈 + 异常信息

        // 2. 返回给前端友好的提示（不要把堆栈暴露给用户）
        String errorMsg = "服务器内部错误，请稍后重试";

        return ResultUtil.fail_50000(errorMsg);
    }
}
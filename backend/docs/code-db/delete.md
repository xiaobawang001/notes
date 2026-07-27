删除扣子数据库中符合条件的数据，支持同步和异步删除模式。
:::tip 说明
* 同步或异步删除数据时，必须通过`filter`字段指定删除范围筛选条件，不允许无条件删除全表。
* 可通过[查询异步执行结果](https://docs.coze.cn/developer_guides/get_async_task_result)接口，查看异步删除执行结果。
:::
## 基础信息 {#基础信息}
<!-- @cols-width: 180,680 -->
| | | \
|**请求方式** |DELETE |
|---|---|
| | | \
|**请求地址** |```Plain Text |\
| |https://api.coze.cn/v1/databases/:database_id/records |\
| |``` |\
| | |
| | | \
|**权限** |`Database.deleteRecord` |\
| |确保调用该接口使用的访问令牌开通了`Database.deleteRecord`权限，详细信息参考[鉴权方式](https://docs.coze.cn/developer_guides/authentication)。 |
| | | \
|**接口说明** |删除数据库中符合条件的记录必须提供过滤条件。 |

## 请求参数 {#请求参数}
### Header {#Header}
<!-- @cols-width: 144,165,551 -->
| | | | \
|**参数** |**取值** |**说明** |
|---|---|---|
| | | | \
|Authorization |Bearer *$Access_Token* |用于验证客户端身份的访问令牌。你可以在扣子平台中生成访问令牌，详细信息，参考[准备工作](https://www.coze.cn/docs/developer_guides/preparation)。 |
| | | | \
|Content-Type |application/json |解释请求正文的方式。 |

### Path {#Path}
<!-- @cols-width: 133,122,87,165,340 -->
| | | | | | \
|**参数** |**类型** |**是否必选** |**示例** |**说明** |
|---|---|---|---|---|
| | | | | | \
|database_id |String |必选 |761070127115408**** |要删除数据的数据库 ID。 |

### Body {#Body}
<!-- @cols-width: 146,121,86,165,328 -->
| | | | | | \
|**参数** |**类型** |**是否必选** |**示例** |**说明** |
|---|---|---|---|---|
| | | | | | \
|filter |Object of [OpenComplexCondition](#opencomplexcondition) |必选 |{"logic":"or","conditions":[{"left":"user_id","operation":"equal","right":"amy"},{"left":"user_id","operation":"equal","right":"molly"}]} |删除范围筛选条件，指定需删除的数据行。必须提供以避免误删除全表数据。支持通过逻辑运算符 `and` 或 `or`组合多个条件。每个条件包含字段名、操作符和比较值。 |
| | | | | | \
|is_async |Boolean |可选 |false |是否以异步方式执行删除操作。 |\
| | | | | |\
| | | | |* `true`：异步删除，接口将立即返回，删除操作在后台执行。 |\
| | | | |* `false`（默认值）：同步删除，接口将在删除操作完成后返回。 |
| | | | | | \
|connector_id |String |可选 |10000011 |渠道 ID。扣子编程的渠道 ID 包括： |\
| | | | | |\
| | | | |* 1024（默认值）：API 渠道。 |\
| | | | |* 999：Chat SDK。 |\
| | | | |* 10000122：扣子商店。 |\
| | | | |* 10000113：微信客服。 |\
| | | | |* 10000120：微信服务号。 |\
| | | | |* 10000121：微信订阅号。 |\
| | | | |* 10000126：抖音小程序。 |\
| | | | |* 10000127：微信小程序。 |\
| | | | |* 10000011：飞书。 |\
| | | | |* 998：WebSDK。 |\
| | | | |* 自定义渠道 ID。自定义渠道 ID 的获取方式如下：在扣子编程左下角单击头像，在**账号设置** > **发布渠道** > **企业自定义渠道管理**页面查看渠道 ID。 |

### OpenComplexCondition {#opencomplexcondition}
<!-- @cols-width: 131,122,87,165,342 -->
| | | | | | \
|**参数** |**类型** |**是否必选** |**示例** |**说明** |
|---|---|---|---|---|
| | | | | | \
|logic |String |可选 |and |指定多个删除条件之间的逻辑关系。取值如下： |\
| | | | | |\
| | | | |* `and`：所有条件必须同时满足。 |\
| | | | |* `or`：满足任意一个条件即可。 |
| | | | | | \
|conditions |Array of [OpenCondition](#opencondition) |可选 |[{"left":"user_id","operation":"equal","right":"amy"},{"left":"user_id","operation":"equal","right":"molly"}] |指定删除条件的列表，每个条件包含左值（字段名）、操作符和右值（比较目标值）。 |

### OpenCondition {#opencondition}
<!-- @cols-width: 116,122,87,166,356 -->
| | | | | | \
|**参数** |**类型** |**是否必选** |**示例** |**说明** |
|---|---|---|---|---|
| | | | | | \
|left |String |可选 |status |指定删除条件的左值，即需要进行比较的字段名。 |
| | | | | | \
|operation |String |可选 |equal |指定删除条件中的操作符，取值如下： |\
| | | | | |\
| | | | |* `equal`：等于 |\
| | | | |* `not_equal`：不等于 |\
| | | | |* `greater_than`：大于 |\
| | | | |* `less_than`：小于 |\
| | | | |* `greater_equal`：大于等于 |\
| | | | |* `less_equal`：小于等于 |\
| | | | |* `in`：包含在 |\
| | | | |* `not_in`：不包含在 |\
| | | | |* `is_null`：为空 |\
| | | | |* `is_not_null`：不为空 |\
| | | | |* `like`：模糊匹配 |\
| | | | |* `not_like`：模糊不匹配 |
| | | | | | \
|right |String |可选 |amy |指定删除条件中的比较目标值，即与 `left` 字段指定的字段进行比较的值。当 `operation` 为 `is_null` 或 `is_not_null`时，无需填写此字段。 |


## 返回参数 {#返回参数}
<!-- @cols-width: 164,147,164,385 -->
| | | | | \
|**参数** |**类型** |**示例** |**说明** |
|---|---|---|---|
| | | | | \
|data |Object of [DeleteData](#deletedata) |{"affected_rows":28} |返回删除的数据行数。 |
| | | | | \
|code |Long |0 |调用状态码。 |\
| | | | |\
| | | |* 0 表示调用成功。 |\
| | | |* 其他值表示调用失败。你可以通过 msg 字段判断详细的错误原因。 |
| | | | | \
|msg |String |"" |状态信息。API 调用失败时可通过此字段查看详细错误信息。 |\
| | | |状态码为 0 时，msg 默认为空。 |
| | | | | \
|detail |Object of [ResponseDetail](#responsedetail) |{"logid":"20241210152726467C48D89D6DB2****"} |包含请求的详细信息的对象，主要用于记录请求的日志 ID 以便于排查问题。 |

### DeleteData {#deletedata}
<!-- @cols-width: 149,147,165,399 -->
| | | | | \
|**参数** |**类型** |**示例** |**说明** |
|---|---|---|---|
| | | | | \
|task_id |String |7525340985**** |异步删除操作时返回的任务 ID，可通过[GetAsyncTaskResult](https://docs.coze.cn/developer_guides/get_async_task_result)接口查询异步删除执行结果。 |
| | | | | \
|affected_rows |Integer |28 |同步删除时返回成功删除的行数。 |

### ResponseDetail {#responsedetail}
<!-- @cols-width: 100,149,166,445 -->
| | | | | \
|**参数** |**类型** |**示例** |**说明** |
|---|---|---|---|
| | | | | \
|logid |String |20241210152726467C48D89D6DB2**** |本次请求的日志 ID。如果遇到异常报错场景，且反复重试仍然报错，可以根据此`logid`及错误码联系扣子团队获取帮助。详细说明可参考[获取帮助和技术支持](https://docs.coze.cn/guides/help_and_support)。 |

## 示例 {#示例}
### 请求示例 {#请求示例}
```JSON
curl --location --request DELETE 'https://api.coze.cn/v1/databases/761284025805235****/records' \
--header 'Authorization: Bearer pat_O******' \
--header 'Content-Type: application/json' \
--data-raw '{
  "connector_id": "10000011",  
  "filter": {
    "logic": "or",
    "conditions": [
      {
        "left": "user_id",
        "operation": "equal",
        "right": "amy"
      },
      {
        "left": "user_id",
        "operation": "equal",
        "right": "molly"
      }
    ]
  },
  "is_async": true
}'
```

### 返回示例 {#返回示例}
```JSON
{
    "code": 0,
    "data": {
        "task_id": "7525340985****"
    },
    "msg": "",
    "detail": {
        "logid": "20241210152726467C48D89D6DB2****"
    }
}
```

## 错误码 {#错误码}
如果成功调用扣子编程的 API，返回信息中 code 字段为 0。如果状态码为其他值，则表示接口调用失败。此时 msg 字段中包含详细错误信息，你可以参考[错误码](https://docs.coze.cn/developer_guides/coze_error_codes)文档查看对应的解决方法。


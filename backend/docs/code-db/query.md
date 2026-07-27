查询扣子数据库中的记录，支持条件过滤、排序、分页，支持同步和异步查询模式。
:::tip 说明
可通过[查询异步执行结果](https://docs.coze.cn/developer_guides/get_async_task_result)接口，查看异步查询任务执行结果。
:::
## 基础信息 {#基础信息}
<!-- @cols-width: 180,680 -->
| | | \
|**请求方式** |POST |
|---|---|
| | | \
|**请求地址** |```Plain Text |\
| |https://api.coze.cn/v1/databases/:database_id/records/query |\
| |``` |\
| | |
| | | \
|**权限** |`Database.readRecord` |\
| |确保调用该接口使用的访问令牌开通了`Database.readRecord`权限，详细信息参考[鉴权方式](https://docs.coze.cn/developer_guides/authentication)。 |
| | | \
|**接口说明** |查询扣子数据库中的记录。 |

## 请求参数 {#请求参数}
### Header {#Header}
<!-- @cols-width: 144,165,551 -->
| | | | \
|**参数** |**取值** |**说明** |
|---|---|---|
| | | | \
|Authorization |Bearer *$Access_Token* |用于验证客户端身份的访问令牌。你可以在扣子编程中生成访问令牌，详细信息，参考[准备工作](https://www.coze.cn/docs/developer_guides/preparation)。 |
| | | | \
|Content-Type |application/json |解释请求正文的方式。 |

### Path {#Path}
<!-- @cols-width: 133,122,87,165,340 -->
| | | | | | \
|**参数** |**类型** |**是否必选** |**示例** |**说明** |
|---|---|---|---|---|
| | | | | | \
|database_id |String |必选 |761070127115408**** |需要执行查询操作的数据库 ID。 |

### Body {#Body}
<!-- @cols-width: 147,121,86,165,327 -->
| | | | | | \
|**参数** |**类型** |**是否必选** |**示例** |**说明** |
|---|---|---|---|---|
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
| | | | | | \
|select_fields |Object of [OpenSelectFieldList](#openselectfieldlist) |可选 |{"field_names":["user_id","level"],"is_distinct":false} |指定查询时需要返回的字段列表，支持配置字段名数组和是否去重的规则，默认不去重。 |
| | | | | | \
|order_by |Array of [OpenOrderBy](#openorderby) |可选 |[{"field_name": "level",    "direction": "asc"}] |指定查询结果的排序规则，支持按多个字段进行排序。每个排序规则由字段名（field_name）和排序方向（direction）组成，排序方向支持升序（asc）或降序（desc）。 |
| | | | | | \
|page_num |Integer |可选 |1 |当前查询的页码，用于分页查询。默认值为 `1`。 |
| | | | | | \
|page_size |Integer |可选 |20 |每页返回的记录数量，用于分页查询。默认值为 `20`，最大值为 `1000`。 |
| | | | | | \
|filter |Object of [OpenComplexCondition](#opencomplexcondition) |可选 |{"logic":"and","conditions":[{"left":"user_id","operation":"equal","right":"amy"}]} |查询条件，用于筛选符合条件的记录。支持逻辑关系（`and` 或 `or`）和多个条件的组合。每个条件包含左值（字段名）、操作符和右值（比较目标值）。 |
| | | | | | \
|is_async |Boolean |可选 |false |是否启用异步查询模式，取值如下： |\
| | | | | |\
| | | | |*  `true`：启用异步查询模式。 |\
| | | | |*  `false`（默认值）：启用同步查询模式。 |

### OpenSelectFieldList {#openselectfieldlist}
<!-- @cols-width: 132,122,87,165,341 -->
| | | | | | \
|**参数** |**类型** |**是否必选** |**示例** |**说明** |
|---|---|---|---|---|
| | | | | | \
|field_names |Array of String |可选 |["user_id","level"] |指定查询时需要返回的字段名称列表，支持多个字段的组合。若不指定，默认返回所有字段。 |
| | | | | | \
|is_distinct |Boolean |可选 |false |是否对查询结果进行去重处理，取值如下： |\
| | | | | |\
| | | | |*  `true`：对查询结果进行去重，返回不重复的记录。 |\
| | | | |*  `false`（默认值）：不对查询结果进行去重，返回所有匹配记录。 |

### OpenOrderBy {#openorderby}
<!-- @cols-width: 124,122,87,165,349 -->
| | | | | | \
|**参数** |**类型** |**是否必选** |**示例** |**说明** |
|---|---|---|---|---|
| | | | | | \
|direction |String |可选 |create_time |排序字段名。 |
| | | | | | \
|field_name |String |可选 |desc |排序方式，取值如下： |\
| | | | | |\
| | | | |* `asc`（默认值）：升序 |\
| | | | |* `desc`：降序 |

### OpenComplexCondition {#opencomplexcondition}
<!-- @cols-width: 131,122,87,165,342 -->
| | | | | | \
|**参数** |**类型** |**是否必选** |**示例** |**说明** |
|---|---|---|---|---|
| | | | | | \
|logic |String |可选 |and |指定多个查询条件之间的逻辑关系。取值如下： |\
| | | | | |\
| | | | |* `and`：所有条件必须同时满足。 |\
| | | | |* `or`：满足任意一个条件即可。 |
| | | | | | \
|conditions |Array of [OpenCondition](#opencondition) |可选 |[{"left": "user_id", "operation": "equal", "right": "amy"}] |指定查询条件的列表，每个条件包含左值（字段名）、操作符和右值（比较目标值）。 |

### OpenCondition {#opencondition}
<!-- @cols-width: 116,122,87,166,356 -->
| | | | | | \
|**参数** |**类型** |**是否必选** |**示例** |**说明** |
|---|---|---|---|---|
| | | | | | \
|left |String |可选 |status |指定查询条件的左值，即需要进行比较的字段名。 |
| | | | | | \
|operation |String |可选 |equal |指定查询条件中的操作符，取值如下： |\
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
|right |String |可选 |amy |指定查询条件中的比较目标值，即与 `left` 字段指定的字段进行比较的值。当 `operation` 为 `is_null` 或 `is_not_null`时，无需填写此字段。 |


## 返回参数 {#返回参数}
<!-- @cols-width: 141,147,165,407 -->
| | | | | \
|**参数** |**类型** |**示例** |**说明** |
|---|---|---|---|
| | | | | \
|data |Object of [SelectData](#selectdata) |{"items":[{"level":"2","user_id":"amy"}],"has_more":false,"total_count":1} |查询时返回的数据信息。 |
| | | | | \
|code |Long |0 |调用状态码。 |\
| | | | |\
| | | |* 0 表示调用成功。 |\
| | | |* 其他值表示调用失败。你可以通过 msg 字段判断详细的错误原因。 |
| | | | | \
|msg |String | |状态信息。API 调用失败时可通过此字段查看详细错误信息。 |\
| | | |状态码为 0 时，msg 默认为空。 |
| | | | | \
|detail |Object of [ResponseDetail](#responsedetail) |{"logid":"20241210152726467C48D89D6DB2****"} |包含请求的详细信息的对象，主要用于记录请求的日志 ID 以便于排查问题。 |

### SelectData {#selectdata}
<!-- @cols-width: 126,148,165,421 -->
| | | | | \
|**参数** |**类型** |**示例** |**说明** |
|---|---|---|---|
| | | | | \
|items |Array of JSON Map |[{"level":"2","user_id":"amy"}] |同步查询时返回的记录列表，每条记录以键值对形式表示字段及其对应的值。 |
| | | | | \
|task_id |String |7525340985**** |异步查询时返回的任务 ID。可通过[查询异步执行结果](https://docs.coze.cn/developer_guides/get_async_task_result)接口，查看异步查询任务执行结果。 |
| | | | | \
|has_more |Boolean |false |标识当前同步查询结果是否还有数据未返回。 |\
| | | | |\
| | | |*  `true` ：表示存在更多数据，可通过调整分页参数继续查询。 |\
| | | |*  `false`：表示已返回所有数据。 |
| | | | | \
|total_count |Integer |1 |同步查询时返回的总记录数，表示符合查询条件的记录总数。 |

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
curl --location --request POST 'https://api.coze.cn/v1/databases/761284025805235****/records/query' \
--header 'Authorization: Bearer pat_O****' \
--header 'Content-Type: application/json' \
--data-raw '{
    "connector_id": "10000011",    
    "select_fields": {
        "field_names": [
            "user_id",
            "level"
        ],
        "is_distinct": false
    },
    "page_num": 1,
    "page_size": 10,
    "filter": {
        "logic": "and",
        "conditions": [
            {
                "left": "user_id",
                "operation": "equal",
                "right": "amy"
            }
        ]
    },
    "is_async": false
}'
```

### 返回示例 {#返回示例}
```JSON
{
    "data": {
        "items": [
            {
                "level": "2",
                "user_id": "amy"
            }
        ],
        "has_more": false,
        "total_count": 1
    },
    "msg": "",
    "detail": {
        "logid": "20241210152726467C48D89D6DB2****"
    },
    "code": 0
}
```

## 错误码 {#错误码}
如果成功调用扣子编程的 API，返回信息中 code 字段为 0。如果状态码为其他值，则表示接口调用失败。此时 msg 字段中包含详细错误信息，你可以参考[错误码](https://docs.coze.cn/developer_guides/coze_error_codes)文档查看对应的解决方法。


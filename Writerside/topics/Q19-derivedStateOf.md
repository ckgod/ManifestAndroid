# Q19) derivedStateOf

## derivedStateOf의 목적은 무엇이고 리컴포지션을 어떻게 최적화하나요? {#what-is-derivedstateof}

`derivedStateOf` 는 하나 이상의 상태 객체로부터 파생된 값을 계산하는 컴포저블 API입니다. 의존하는 상태가 바뀔 때만 파생값을 다시 계산하므로, 반응형 상태 관계를 효율적으로 다루는 데 효과적입니다.

핵심 특징은 **실제로 계산된 값 자체가 바뀐 경우에만 리컴포지션을 트리거** 한다는 점입니다. 의존하는 상태가 자주 바뀌더라도, 파생값이 동일하면 리컴포지션을 일으키지 않으므로, 빈번한 상태 갱신이 있는 상황에서 불필요한 리컴포지션을 줄이는 데 특히 유용합니다.

다만 `derivedStateOf` 는 자체적으로 약간의 계산 오버헤드를 가집니다. 그래서 **리컴포지션 회피가 정말 중요한 자리에서만** 사용하는 것이 좋고, 얻는 이익이 비용보다 큰지 따져 보는 것이 좋습니다.

### 언제 사용하면 좋은가 {#when-to-use}

- **파생 데이터(Derived Data)**: 기존 상태로부터 필터링된 리스트나 결합된 텍스트 같은 값을 계산해야 할 때.
- **리컴포지션 회피**: 자주 바뀌는 상태에 의존하지만, 파생값이 변할 때만 리컴포지션을 일으키고 싶을 때.

### 사용 예시 {#how-to-use}

검색어를 기반으로 항목 리스트를 필터링하는 실용적인 예시입니다.

```kotlin
@Composable
fun DerivedStateExample(items: List<String>, searchQuery: String) {
    val filteredItems by remember(searchQuery, items) {
        derivedStateOf {
            items.filter { it.contains(searchQuery, ignoreCase = true) }
        }
    }

    Column {
        Text("Search results:")
        filteredItems.forEach { item ->
            Text(item)
        }
    }
}
```
{title="DerivedStateOfExample.kt"}

이 예시에서는 `filteredItems` 가 `items` 와 `searchQuery` 로부터 파생되며, `derivedStateOf` 가 이 두 상태가 바뀔 때만 리스트를 다시 계산하도록 보장합니다.

### derivedStateOf의 동작 {#how-it-works}

1. 람다 안에서 접근하는 상태들을 관찰합니다.
2. 관찰 중인 상태가 바뀌면 새 값을 계산합니다.
3. 새로 계산된 값이 이전 값과 **다른 경우에만** 리컴포지션을 트리거합니다.

### 사용 시 주의할 점 {#key-points}

- `remember` 와 함께 사용해 파생 상태가 리컴포지션을 가로질러 보존되도록 합니다.
- `derivedStateOf` 블록 안에는 무거운 계산을 두지 않습니다. 매끄러운 성능을 위해 가벼운 계산만 둡니다.
- 불필요한 리컴포지션을 정말 줄여야 하는 자리에서만 절제해서 사용합니다.

### 응용 예시: 실시간 파생 상태 {#advanced-example}

```kotlin
@Composable
fun RealTimeDerivedStateExample() {
    var text by remember { mutableStateOf("") }
    val isInputValid by remember {
        derivedStateOf { text.length >= 5 }
    }

    Column {
        TextField(value = text, onValueChange = { text = it })
        if (isInputValid) {
            Text("Valid input")
        } else {
            Text("Input must be at least 5 characters")
        }
    }
}
```
{title="RealTimeDerivedStateExample.kt"}

이 예시에서 입력 유효성(`isInputValid`)은 `text` 상태로부터 파생됩니다. UI는 `text` 가 바뀔 때마다 다시 그려지지 않고, **`isInputValid` 가 바뀔 때만** 리컴포지션이 일어납니다.

### 잘못된 사용 예시 {#incorrect-usage}

두 개의 Compose 상태 객체를 결합할 때 흔히 저지르는 실수가 "이건 상태에서 파생된 값이니까 항상 `derivedStateOf` 를 써야 한다" 고 가정하는 것입니다. 다음 예시처럼 많은 경우에는 오히려 불필요한 오버헤드만 더할 뿐입니다.

```kotlin
// 잘못된 사용: derivedStateOf 가 필요 없는 자리
var firstName by remember { mutableStateOf("") }
var lastName by remember { mutableStateOf("") }

val fullNameBad by remember { derivedStateOf { "$firstName $lastName" } } // 비효율적
val fullNameCorrect = "$firstName $lastName" // 더 효율적
```
{title="IncorrectDerivedStateExample.kt"}

이 코드에서 `fullName` 은 `firstName` 과 `lastName` 이 바뀔 때마다 그대로 갱신되어야 하므로, 그 자체가 의도된 동작입니다. 즉 과잉 리컴포지션이 일어나는 상황이 아니므로 `derivedStateOf` 로 감싸는 것은 단지 비용만 더하는 셈입니다. `derivedStateOf` 는 "의존 상태가 바뀐다고 해도 결과값이 같으면 리컴포지션을 막아 주는" 효과가 의미 있을 때만 사용해야 합니다.

### 요약 {#summary}

<tldr>

`derivedStateOf` 는 반응형이며 최적화된 파생 상태를 만들기 위한 부수 효과 핸들러 API입니다. 정말 필요할 때만 리컴포지션을 트리거하므로 UI 효율을 높이고 코드를 더 선언적으로 만들어 줍니다. 복잡한 상태 관계를 효율적으로 다루면서도 성능과 명료함을 유지하는 데 유용한 도구입니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 어떤 상황에서 derivedStateOf 를 사용하고, 어떤 상황에서는 다른 상태 변수로부터 값을 계산해도 derivedStateOf 를 피해야 하나요?">

`derivedStateOf` 가 진가를 발휘하는 자리는 **의존 상태는 자주 바뀌지만 파생값은 드물게 바뀌는 경우** 입니다. 대표적인 예가 본문에서도 다룬 "스크롤 위치가 임계치를 넘었는가" 같은 boolean 파생값입니다. `LazyListState` 의 인덱스는 1픽셀 단위로 갱신될 정도로 자주 바뀌지만, 그 정보를 토대로 만든 boolean은 한참 동안 같은 값을 유지합니다. 이런 자리에 `derivedStateOf` 를 두면, 의존 상태가 매 프레임 갱신되더라도 파생값이 같은 동안에는 리컴포지션이 일어나지 않습니다. 비슷한 패턴으로 검색어와 항목 리스트를 결합한 필터 결과, 폼 전체 유효성, 표시할 다이얼로그 종류 같은 파생값이 모두 후보가 됩니다.

반대로 `derivedStateOf` 가 필요 없는 자리도 분명히 있습니다. **의존 상태와 파생값이 거의 같은 빈도로 바뀌는 경우** 가 그것입니다. 본문의 `firstName + lastName → fullName` 예시처럼, 의존 상태가 바뀌면 결과도 거의 매번 바뀐다면 `derivedStateOf` 로 감싼다고 해서 줄어드는 리컴포지션이 없습니다. 오히려 매 호출마다 람다 평가와 동등성 비교 비용만 추가됩니다. 단순한 문자열/숫자 결합이나 단일 상태에서 바로 도출되는 값은 그냥 `val derived = ...` 형태로 두는 편이 훨씬 가볍습니다.

판단 기준을 한 줄로 요약하면 "의존 상태의 변경 빈도와 파생값의 변경 빈도 사이에 의미 있는 간극이 있는가?" 입니다. 간극이 클수록 `derivedStateOf` 의 가치도 커집니다. 또한 `remember(key1, key2) { derivedStateOf { ... } }` 형태로 키를 명시해 두면, 파라미터가 바뀌었을 때 파생 상태가 새로 만들어지면서 stale snapshot에 의존하지 않도록 막을 수 있습니다. 마지막으로 람다 안에서는 무거운 연산을 피하고, 정말 무거운 작업이라면 `derivedStateOf` 가 아니라 ViewModel 레벨의 상태 변환으로 끌어올리는 것이 일반적으로 더 깔끔한 선택입니다.

</def>
</deflist>

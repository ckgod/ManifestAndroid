# Q11) State

## State란 무엇이며, 이를 관리하는 데 사용되는 API는 무엇인가요?
Jetpack Compose에서 [State](https://developer.android.com/develop/ui/compose/state)는 시간 경과에 따라 변경될 수 있는 모든 값을 지칭하며, 앱 UI의 동적인 측면을 나타냅니다.
앱 내 State의 예시로는 네트워크 오류에 대한 Snackbar 메시지, 양식에 입력된 사용자 입력, 또는 상호작용으로 인해 트리거되는 애니메이션 등이 있습니다. 

State는 Compose와 같은 선언형 프레임워크에서 UI 업데이트를 직접적으로 주도하기 때문에 매우 중요합니다. <br>
Compose는 현재 State를 기반으로 composable을 평가하여 UI를 렌더링하고, State가 변경되면 이들을 다시 평가합니다.

### State와 Composition
Jetpack Compose는 선언형 UI 접근 방식을 따릅니다. 
이는 UI 업데이트가 업데이트된 인수로 composable이 호출될 때만 발생한다는 것을 의미합니다.
이러한 동작은 composition 수명 주기와 밀접하게 관련되어 있습니다.

*   **초기 Composition (Initial Composition)**: composable을 실행하여 UI 트리가 처음 생성되고 렌더링되는 과정입니다.
*   **Recomposition**: State가 변경될 때 트리거되며, 관련 composable을 업데이트하여 새 State를 반영합니다.
    Compose Runtime은 전통적인 Android View 시스템에서처럼 `View.invalidate()`와 같은 수동 호출 없이 State 변경 사항을 자동으로 추적하고 UI를 업데이트합니다. <br> Recomposition은 업데이트된 State를 반영해야 하는 composable 함수에 대해서만 트리거됩니다. 아래 예시는 State 변경 사항이 UI에 자동으로 적용되는 방식을 보여줍니다.

```Kotlin
@Composable
fun HelloContent() {
    Column(modifier = Modifier.padding(16.dp)) {
        var name by remember { mutableStateOf("") }

        if (name.isNotEmpty()) {
            Text(text = "Hello, $name!", modifier = Modifier.padding(bottom = 8.dp))
        }

        TextField(
            value = name,
            onValueChange = { name = it },
            label = { Text("Name") }
        )
    }
}
```

여기서 `name` State가 변경되면 Text 및 TextField composable이 자동으로 업데이트되어 UI가 최신 State와 동기화됩니다.

### Compose에서 State 관리하기
Jetpack Compose는 State를 효과적으로 관리하기 위한 여러 도구를 제공합니다.
1.  **remember**: 초기 composition 동안 객체를 메모리에 저장하고 recomposition 중에 이를 검색합니다.
    ```Kotlin
        var count by remember { mutableStateOf(0) }
    ```
2.  **rememberSaveable**: 화면 회전과 같은 구성 변경에도 State를 유지합니다. `Bundle`에 저장될 수 있는 유형이나 다른 유형에 대한 사용자 지정 saver 객체와 함께 작동합니다.
3.  **mutableStateOf**: 값이 변경될 때 recomposition을 트리거하는 관찰 가능한 State 객체를 생성합니다. 아래 예시와 같이 `remember`와 `mutableStateOf`를 함께 사용하여 State 객체를 메모리에 저장할 수 있습니다.

    ```Kotlin
        val mutableState = remember { mutableStateOf("") }
        var value by remember { mutableStateOf("") }
        val (value, setValue) = remember { mutableStateOf("") }
    ```

> **추가 팁**: `mutableStateOf`와 함께 `remember`를 사용해야 하는 이유는 무엇일까요? 위 설명을 읽으면서 이 질문을 스스로에게 던졌다면 제대로 이해하고 있는 것입니다. 일반적으로 사용되는 API가 실제로 어떻게 작동하는지에 대해 질문하는 것은 더 나은 개발자로 성장하는 데 도움이 되는 호기심입니다. `remember` API는 recomposition 간에 객체를 메모리에 저장하는 데 사용됩니다. 반면에 `mutableStateOf`는 State가 변경될 때 recomposition을 트리거하는 **관찰 가능한 State 홀더**를 생성합니다.
>
> 그렇다면 `remember` 없이 `mutableStateOf`만 사용하면 어떻게 될까요? 이 경우, recomposition이 발생할 때마다 `mutableStateOf`에 저장된 값이 메모리에 보존되지 않으므로 다시 초기화됩니다. 결과적으로, State가 제대로 보존되지 않아 컴포넌트가 예상대로 작동하지 않을 수 있습니다.
> 이것이 `remember`를 사용하여 recomposition 간에 State가 메모리에 저장되도록 하여 UI 로직을 안정적이고 예측 가능하게 유지하는 것이 중요한 이유입니다.

### 요약
State는 Jetpack Compose의 초석이며, 데이터 변경 사항과 UI를 동기화하기 위해 자동 recomposition을 가능하게 합니다.
State가 recomposition을 효율적으로 트리거하기 때문에 개발자는 UI 계층 구조를 수동으로 업데이트하고 다시 렌더링할 필요가 없습니다.
그러나 의도치 않은 recomposition이 발생하여 성능이 저하될 수도 있습니다.
State가 어떻게 작동하는지 이해하는 것은 효율적이고 성능이 좋은 Compose 애플리케이션을 구축하는 데 중요합니다.

> Q) State는 recomposition과 어떻게 관련되어 있으며, recomposition 동안 어떤 일이 발생하나요?

#### A) {collapsible="true"}
Compose에서 State는 Recomposition을 유발하는 **트리거** 역할을 합니다.

State 객체(예: `mutableStateOf()`로 생성)의 .value가 변경되면, Compose 런타임은 해당 State 값을 읽고 있는 Composable 함수들만 다시 실행(Recomposition)하도록 스케줄링합니다.

Recomposition 동안 발생하는 일
1. 변경 감지: State의 value 변경 감지
2. 스케줄링: Compose 런타임이 해당 State를 읽는 가장 가까운 restartable한 Composable 스코프를 Recomposition 큐에 추가
3. 재실행: 다음 프레임에서 Compose 런타임이 큐에있는 Composable 함수들을 다시 호출
4. 비교 및 스킵:  
   - Compose는 함수를 다시 실행하면서 생성되는 UI 트리(노드)를 이전의 UI트리와 비교
   - 재실행되는 함수 내의 자식 Composable이 받는 모든 input이 이전과 동일하고, 해당 매개변수 타입이 Stable이면 Compose는 그 자식 Composable 함수의 recomposition을 스킵
   - 변경된 부분만 실제 UI에 반영

Compose 컴파일러가 Stable을 판단하는 방법
- 이 타입이 변경되었는지 equals() 비교만으로 100% 신뢰할 수 있는가?

1. 기본적으로 Stable한 타입
- Primitive 타입: Int, Float, Boolean, String 등
- 함수 타입(람다): () -> Unit, (Int) -> String 등

2. 컴파일러의 추론
- data class
  - 모든 public 속성이 val이고, 그 val들의 타입 또한 모두 Stable 이라면 해당 data class는 Stable로 추론
- 컬렉션
  - `List<T>`, `Set<T>`, `Map<K, V>` 등
  - 제네릭 타입이 모두 Stable 해야만 해당 컬렉션이 Stable로 간주

3. 명시적 어노테이션
직접 컴파일러에게 이 타입은 Stable하다고 알려주는 방식
- `@Immutable`: "이 클래스는 절대 불변입니다."
  - `data class`의 모든 속성이 val이고 타입이 Stable할 때 컴파일러가 추론하는 것과 동일한 효과
  - 컴파일러가 추론하지 못하는 불변 클래스(예: `interface`를 구현)에 사용합니다.
- `@Stable`: "이 클래스는 변경될 수 있지만, 변경되면 Compose 런타임에 반드시 알립니다."
  - 대표적인 예시가 `MutableState<T>`
  - `MutableState`의 `.value`는 변경 가능하지만, 변경될 때 런타임에 "나 변경됐어!"라고 알리기 때문에 Compose는 이 타입을 Stable로 신뢰한다.
  - 변경됐으면 알려준다 -> 변경됐으면 recomposition 무조건 실행, equals 비교도 신뢰 가능




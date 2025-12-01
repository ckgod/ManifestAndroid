# Q20) Composable 생명 주기

## Composable 함수 또는 Composition의 생명 주기란 무엇인가요?
Composable 함수는 Android View나 Activity와 같은 전통적인 생명 주기를 가지지 않습니다.
대신, Compose 런타임에 의해 구동되는 Composition-aware 생명 주기를 따릅니다.

![composable-lifecycle.png](composable-lifecycle.png)

이 생명 주기는 UI 상태가 변경될 때 Composable 함수가 효율적으로 호출되고, Recomposition되며, 제거되도록 보장합니다.
아래는 Composable 함수의 생명 주기에서 주요 단계에 대한 설명입니다:

### 1. 초기 Composition
이것은 Composable 함수가 실행될 때의 첫 번째 단계입니다. 

이 단계에서:
*   함수는 주어진 상태를 기반으로 초기 UI 요소를 생성합니다.
*   LaunchedEffect 또는 remember와 같은 모든 Side-effect는 초기화되어 향후 Recomposition을 위해 기억됩니다.
*   UI 계층 구조가 구축되고 Composition 트리에 추가됩니다.
    예를 들어, 다음 `Greeting` 함수는 주어진 매개변수 값 `name`에 대해 초기 Composition을 구성합니다.

```kotlin
@Composable
fun Greeting(name: String) {
    Text(text = "Hello, $name!")
}
```

### 2. Recomposition

Composable 함수가 의존하는 상태가 변경될 때 Recomposition이 발생합니다. 

Recomposition 중에는:
*   Composition 트리의 영향을 받는 부분만 Recomposition됩니다 (스마트 Recomposition).
*   Compose는 업데이트가 필요 없는 UI 트리의 부분을 건너뛰어 프로세스를 최적화합니다.
*   remember에 의해 관리되는 Side-effect는 Recomposition 전반에 걸쳐 유지됩니다.
    예를 들어, `count`가 변경될 때 버튼 내부의 `Text`만 Recomposition됩니다.

```kotlin
@Composable
fun Counter() {
    var count by remember { mutableStateOf(0) }

    Button(onClick = { count++ }) {
        Text(text = "Clicked $count times")
    }
}
```

### 3. Composition 이탈

Composable 함수가 Composition에서 제거될 때(예를 들어, 다른 화면으로 이동할 때) Composition을 이탈합니다. 이 단계에서는 다음 작업이 수행됩니다:
*   Composable과 관련된 모든 리소스는 자동으로 정리됩니다.
*   DisposableEffect와 같은 Side-effect는 리소스를 해제합니다.
*   rememberCoroutineScope는 실행 중인 모든 Coroutine 작업을 안전하게 취소합니다.
    예를 들어, Composable이 DisposableEffect 내에서 Composition을 이탈할 때 `onDispose` 블록이 호출됩니다.

```kotlin
@Composable
fun DisposableExample() {
    DisposableEffect(Unit) {
        println("Entering composition")
        onDispose {
            println("Leaving composition")
        }
    }
    Text(text = "Composable in use")
}
```

### Composition 생명 주기의 주요 사항
*   **Composition의 단계**: Composition 생명 주기는 초기 Composition, Recomposition, 제거의 세 가지 주요 단계로 구성됩니다. 첫 번째 Composition은 Composable 함수가 Composition 트리에 진입할 때 발생하며, Recomposition은 상태 변경이 특정 UI 요소에 대한 업데이트를 트리거할 때 발생합니다.
*   **건너뛰기 및 최적화**: Compose는 변경되지 않은 함수에 대한 Recomposition을 지능적으로 건너뛰어 불필요한 UI 업데이트를 줄입니다. 이는 `remember`, `derivedStateOf` 및 안정적인 상태 관리와 같은 메커니즘을 통해 성능을 향상시킵니다.
*   **제거 및 정리**: Composable 함수가 Composition을 이탈할 때, UI 트리에서 제거됩니다. LaunchedEffect의 `Coroutine`이나 DisposableEffect의 구독(subscription) 또는 `remember`를 사용하여 생성된 상태와 같이 시작된 Side-effect가 있다면, 메모리 누수를 방지하기 위해 적절하게 정리되어야 합니다. 이는 Composition-aware 방식으로 이루어집니다.

### 요약
Composable 함수의 생명 주기는 초기 Composition, Recomposition, 그리고 Composition 이탈의 세 가지 주요 단계로 구성됩니다. 각 단계는 효율적인 렌더링, 반응형 업데이트, 그리고 적절한 리소스 정리를 보장하는 데 중요한 역할을 합니다. Activity, Fragment, ViewModel과 같은 전통적인 Android 컴포넌트의 생명 주기를 이해하는 것이 필수적인 것처럼, Composable 함수의 생명 주기를 올바르게 이해하는 것은 효율적인 UI 컴포넌트를 설계하는 데 핵심입니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Composable 함수의 생명 주기 단계를 설명하고, 상태가 변경될 때 Compose가 Recomposition을 어떻게 처리하는지 설명하세요.">

기본적으로 Composition에 들어오기, Recomposition, Composition에서 나가기 3단계로 요약할 수 있습니다.

1. Composition
   - Composable 함수가 처음 호출되어 UI 트리에 추가되는 단계입니다.
   - remember 및 rememberSaveable을 통해 State와 객체가 초기화되고 메모리에 저장됩니다.
   - LaunchedEffect(Unit) 또는 DisposableEffect(Unit) 의 메인 블록이 실행됩니다.
2. Recomposition
   - Composable이 구독하고 있던 State가 변경되면, 해당 Composable이 다시 호출되는 단계입니다.
   - 이 단계는 앱이 실행되는 동안 매우 빈번하게 발생할 수 있습니다.
   - Compose는 변경되지 않은 Composable은 건너뛰므로 이 과정이 매우 효율적입니다.
   - SideEffect 블록이 이 단계가 성공적으로 완료될 때마다 실행됩니다.
3. Leaving Composition
   - Composable이 더 이상 UI 트리에 필요하지 않아 제거되는 단계입니다.
   - DisposableEffect의 onDispose 블록이 실행되어 리스너 해제와 같은 정리 작업을 수행합니다.

**Recomposition 처리 방식**

1. 상태 구독
   - Composable 함수가 State 객체의 .value 속성을 읽는 순간, Compose는 이 Composable이 State를 구독했다고 자동으로 기록합니다.
2. 상태 변경
   - Button의 onClick 등 어딘가에서 해당 State의 .value가 새로운 값으로 변경됩니다.
   - Compose는 이 상태의 값이 바뀌었다고 인지합니다.
   - 즉시 1단계에서 이 상태를 구독했던 모든 Composable을 무효화(다시 그려야 함) 시킵니다.
3. 재실행 및 비교
   - Compose 스케줄러가 다음 프레임에 무효화된 Composable 함수들만 다시 실행합니다.
   - 이 때 Smart Skipping이 발생합니다.
     - 만약 재실행되는 Composable의 입력 파라미터가 모두 안정적(Stable)이고 변경되지 않았다면, Compose는 이 Composable의 내부는 실행조차 하지 않고 그냥 건너뜁니다.
   - 재실행된 Composable이 반환한 새로운 UI트리를 이전의 UI트리와 비교합니다.
4. 적용
   - 비교 결과, 실제로 변경된 부분만 식별하여 화면에 적용합니다.

</def>
</deflist>
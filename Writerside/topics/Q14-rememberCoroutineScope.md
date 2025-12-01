# Q14) rememberCoroutineScope

## Composable 함수 내에서 Coroutine Scope를 안전하게 생성하는 방법
Jetpack Compose에서 [`rememberCoroutineScope`](https://developer.android.com/develop/ui/compose/side-effects#remembercoroutinescope)를 사용하는 것은 Composable 함수 내에서 Coroutine Scope를 안전하게 생성하고 관리하는 권장 방법입니다. 
이는 Coroutine Scope가 Composition에 연결되어 잠재적인 메모리 누수와 부적절한 리소스 사용을 방지합니다.

### rememberCoroutineScope를 사용하는 이유
Jetpack Compose의 `rememberCoroutineScope`는 Composition을 인식하는 Coroutine Scope를 제공하여, Composable이 Composition을 벗어날 때 활성 Coroutine을 자동으로 취소합니다. 이를 통해 수동적인 Lifecycle 관리가 필요 없이 Composable에서 Coroutine을 안전하게 시작할 수 있습니다.

### 사용 예시

```kotlin
@Composable
fun CounterWithReset() {
    var count by remember { mutableStateOf(0) }
    val coroutineScope = rememberCoroutineScope()

    Column(
        modifier = Modifier.padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text("Count: $count", style = MaterialTheme.typography.h5)
        Spacer(modifier = Modifier.height(8.dp))
        Button(onClick = { count++ }) {
            Text("Increment")
        }
        Spacer(modifier = Modifier.height(8.dp))
        Button(onClick = {
            coroutineScope.launch {
                // 리셋을 위한 지연 시뮬레이션
                delay(1000)
                count = 0
            }
        }) {
            Text("Reset After 1s")
        }
    }
}
```

### 작동 방식
1.  **Composition 인식 (Composition Awareness)**: `rememberCoroutineScope`로 생성된 Coroutine Scope는 Composition에 범위가 지정됩니다. 이는 해당 Scope 내에서 시작된 모든 Coroutine이 Composable이 Composition에서 제거될 때 취소되도록 보장합니다.
2.  **상태 관리 (State Management)**: `remember` API는 Recomposition에서도 유지되어야 하는 상태 값을 보유하고 관리하는 데 사용됩니다. `rememberCoroutineScope`와 함께 사용하면 비동기 작업을 안전하게 관리하는 데 도움이 됩니다.
3.  **메모리 누수 방지 (Avoids Memory Leaks)**: GlobalScope를 사용하거나 Coroutine Scope를 수동으로 관리하는 것과는 달리, `rememberCoroutineScope`는 새로운 Coroutine Scope를 생성하고 Composable이 더 이상 사용되지 않을 때 리소스가 적절하게 정리되도록 보장합니다.

### 모범 사례
*   `rememberCoroutineScope`는 Composition Lifecycle에 연결된 가벼운 UI 관련 작업에 사용하십시오. Composition의 Scope를 넘어 장기간 실행되거나 공유되는 작업의 경우, 적절한 Lifecycle 관리를 보장하고 예기치 않은 취소를 방지하기 위해 `viewModelScope` 또는 `lifecycleScope`와 같은 더 넓은 Scope를 사용하는 것이 좋습니다.
*   Composable 내에서 Coroutine Scope를 직접 생성하는 것은 수동 정리가 필요하고 메모리 누수를 유발할 수 있으므로 피하십시오.
*   `rememberCoroutineScope`를 사용하는 경우에도, 특히 비즈니스 로직과 관련된 Composable 내의 비동기 로직은 제한하고, 더 나은 유지보수성 및 성능을 위해 복잡한 작업은 ViewModel 또는 다른 아키텍처 계층에 위임하십시오.

### 요약
`rememberCoroutineScope`는 Composable 함수 내에서 Coroutine Scope를 생성하기 위한 유용하고 안전한 API입니다. 
Coroutine Scope를 Composition에 연결함으로써 리소스의 적절한 정리를 보장하고 메모리 누수를 방지합니다. 
그러나 기본적으로 Main Thread에서 실행되므로, 신중하게 사용하고 네트워크 요청이나 데이터베이스 쿼리와 같은 비즈니스 로직을 직접 실행하는 것은 피해야 합니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Composable 내에서 Coroutine을 직접 시작할 경우의 위험은 무엇이며, 이를 어떻게 피할 수 있습니까?">

Composable 함수 본문 내에서 코루틴을 직접 시작하는 것은 심각한 버그를 유발할 수 있습니다.

Composable 함수는 recomposition에 의해 언제든, 매우 자주 다시 실행될 수 있습니다.
만약 본문에 `scope.launch` 코드가 있다면, 리컴포지션이 일어날 때마다 새로운 코루틴이 시작됩니다.
사용자가 글자 하나를 입력할 때마다, 또는 관련 상태가 조금이라도 바뀔 때마다 네트워크 요청이나 무거운 계산이 다시 시작되는 것입니다.
이는 엄청난 리소스 낭비와 앱 성능 저하를 일으킵니다.

만일 GlobalScope를 사용했다면 Composable이 dispose되어도 취소되지 않고 계속 실행됩니다.
이 코루틴이 만약 화면의 State를 업데이트하려고 시도한다면, 이미 존재하지 않는 UI를 참조하게 되어 크래시가 발생하거나, Composable에 대한 참조를 계속 붙잡고 있어, 메모리 누수를 일으킵니다.

이를 피하기 위해선 코루틴의 생명주기를 Composable의 생명주기에 맞추는 것이 핵심입니다.
이를 위해 두 가지 목적별 해결책이 있습니다.

1. `LaunchedEffect`: Composable이 화면에 나타났을 때 실행

`LaunchedEffect`는 Composable이 Composition에 처음 추가되었을때 코루틴을 실행하고, Composable이 사라질 때 자동으로 코루틴을 취소하는 가장 이상적인 방법입니다.

2. `rememberCoroutineScope`: 사용자 이벤트로 실행

`LaunchedEffect`는 Composable이 등장할 때 실행됩니다. 만약 버튼 클릭처럼 사용자의 특정 이벤트에 대한 응답으로 코루틴을 시작해야 한다면 `rememberCoroutineScope`를 사용합니다.
이 스코프는 Composable의 생명주기에 바인딩되어, Composable이 사라지면 이 스코프에서 시작된 모든 코루틴도 함께 취소됩니다.

</def>
</deflist>


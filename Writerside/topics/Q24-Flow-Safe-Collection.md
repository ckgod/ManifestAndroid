# Q24) Composable에서 Flow를 안전하게 수집하기

## Composable에서 Kotlin Flow를 어떻게 안전하게 수집해야 메모리 누수를 막을 수 있나요? {#how-to-collect-flow-safely}

UI 상태를 다루거나 데이터 변화에 반응하기 위해 컴포저블 안에서 Flow를 수집하는 일은 흔히 일어납니다. 그런데 잘못 다루면 메모리 누수, 과도한 리컴포지션, 성능 저하 같은 문제로 이어질 수 있습니다. Compose에서 Flow를 안전하게 수집하기 위해 널리 쓰이는 두 가지 접근이 `collectAsState` 와 `collectAsStateWithLifecycle` 입니다. 두 API의 차이를 이해하고 상황에 맞게 골라 쓰는 일이 안정적인 Compose 코드의 출발점입니다.

### collectAsState 사용하기 {#using-collectasstate}

`collectAsState` 는 Flow를 수집해 `State` 객체로 변환해 주는 편리한 API입니다. 변환된 결과를 컴포저블 안에서 그대로 사용할 수 있고, Flow가 새 값을 emit 하면 리컴포지션이 자연스럽게 트리거됩니다.

```kotlin
@Composable
fun UserProfileScreen(viewModel: UserViewModel) {
    val userName by viewModel.userNameFlow.collectAsState(initial = "skydoves")

    Column {
        Text(text = "User: $userName")
    }
}
```
{title="CollectAsState.kt"}

이 예시에서는 `userNameFlow` (Flow 타입)가 State로 수집되며, 새 값이 emit 될 때마다 UI가 리컴포지션됩니다. 관찰은 컴포지션 안에서 시작되어 컴포저블이 컴포지션을 떠날 때 종료됩니다.

`collectAsState` 가 많은 경우에 잘 동작하지만, **Android 수명 주기를 자동으로 따르지는 않습니다.** Android와 무관한(API에 lifecycle 개념이 없는) API이기 때문입니다. 이 말은 컴포저블이 메모리에는 남아 있지만 화면에 보이지 않는 상황(예: 다른 화면으로 이동) 에서도 Flow가 계속 수집된다는 뜻이며, 결과적으로 불필요한 자원 사용이 발생할 수 있습니다.

### collectAsStateWithLifecycle 사용하기 {#using-collectasstatewithlifecycle}

`collectAsStateWithLifecycle` 은 Flow 수집을 UI의 lifecycle 에 묶어 두는 더 안전한 대안입니다. 컴포저블이 포그라운드에 있지 않은 동안에는 자동으로 수집이 일시 중단되어, 불필요한 백그라운드 작업을 방지합니다. `androidx.lifecycle:lifecycle-runtime-compose` 패키지에 포함되어 있으며, 처음부터 Android lifecycle 을 인지하도록 설계되어 있습니다.

```kotlin
@Composable
fun UserProfileScreen(viewModel: UserViewModel) {
    val userName by viewModel.userNameFlow.collectAsStateWithLifecycle(initial = "skydoves")

    Column {
        Text(text = "User: $userName")
    }
}
```
{title="CollectAsStateWithLifecycle.kt"}

`collectAsStateWithLifecycle` 의 핵심 장점은 다음과 같습니다.

- 호스트 Activity/Fragment 의 lifecycle 을 따릅니다.
- UI가 보이지 않거나 앱이 백그라운드로 가면 수집이 자동으로 일시 정지됩니다.
- 더 이상 필요 없을 때 Flow가 계속 흐르지 않도록 막아 메모리 누수를 방지합니다.

### 어떤 API를 골라야 할까 {#choosing-the-right-api}

- **`collectAsState`**: 컴포저블이 컴포지션 안에 있는 동안에는 항상 Flow를 수집해야 하는 경우.
- **`collectAsStateWithLifecycle`**: 컴포저블이 화면에 보이지 않을 때 불필요한 작업을 막기 위해 Android lifecycle 을 따라야 하는 경우.

### 요약 {#summary}

<tldr>

Compose에서 Flow를 안전하게 수집하려면 lifecycle 인지를 빼놓을 수 없습니다. `collectAsState` 는 상태 변화에 따라 리컴포지션이 일어나도록 보장하지만 UI가 보이지 않을 때도 수집을 멈추지 않습니다. `collectAsStateWithLifecycle` 은 UI가 백그라운드일 때 수집을 일시 중단시켜 불필요한 작업과 메모리 누수를 방지합니다. 어떤 API를 선택할지는 "수집을 항상 유지할 것인가, 아니면 lifecycle 에 맞춰 다룰 것인가" 에 달려 있습니다. 더 깊은 자료는 *Consuming flows safely in Jetpack Compose* 글을 참고할 수 있습니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) collectAsState 는 lifecycle을 인지하지 않아 UI가 보이지 않을 때도 수집을 계속해 메모리 누수가 발생할 수 있습니다. 이 문제를 어떻게 해결하시겠습니까?">

가장 직접적인 해결책은 **`collectAsStateWithLifecycle`** 로 교체하는 것입니다. 이 API는 호스트 lifecycle 의 `STARTED` 상태가 유지되는 동안에만 Flow를 수집하고, 백그라운드로 가면 자동으로 수집을 일시 중단시킵니다. 즉 화면에 표시되지 않는 컴포저블이 ViewModel의 Flow를 계속 끌고 있어 백엔드 호출이나 이벤트 처리가 이어지는 문제를 사실상 한 줄 변경으로 해결할 수 있습니다. ViewModel 측에서도 `stateIn(scope, SharingStarted.WhileSubscribed(5_000), initialValue)` 와 짝을 맞춰 두면, UI가 잠깐 사라졌다가 다시 돌아왔을 때 콜드 Flow 가 다시 starts/stops 되는 깜빡임 없이 자연스럽게 이어집니다.

상황에 따라서는 `LaunchedEffect` 와 `repeatOnLifecycle(STARTED)` 의 조합으로 같은 효과를 만들 수도 있습니다. 예컨대 일회성 이벤트(`Channel`, `SharedFlow(replay = 0)`)를 다룰 때는 State로 변환할 만한 값이 아니므로, `LaunchedEffect(lifecycleOwner) { lifecycleOwner.repeatOnLifecycle(STARTED) { events.collect { ... } } }` 형태로 lifecycle-aware 한 수집을 직접 작성하는 편이 자연스럽습니다. 이렇게 하면 토스트, 내비게이션, 다이얼로그 같은 일회성 이벤트가 백그라운드 상태에서 발사되어 사용자가 다시 돌아왔을 때 중복 실행되는 사고를 막을 수 있습니다.

마지막으로 점검해 두면 좋은 부분은 **데이터 소스의 책임 분리** 입니다. 화면에서 lifecycle-aware 수집을 잘해 두더라도, ViewModel 안에서 무한히 활성 상태인 Flow가 자원을 잡고 있다면 전체 누수 위험이 사라지지 않습니다. ViewModel 의 핫 Flow는 `SharingStarted.WhileSubscribed`, 콜드 Flow는 `viewModelScope` 의 자연스러운 취소에 맡기는 식으로 정리해 두면, UI 측 변경 한 번만으로도 대부분의 누수 가능성이 함께 해소됩니다. 결론적으로 `collectAsState` → `collectAsStateWithLifecycle` 로의 교체 + ViewModel 의 sharing 정책 점검이 가장 단단한 한 쌍의 수정입니다.

</def>
</deflist>

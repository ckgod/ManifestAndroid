# Q80) UDF와 MVVM·MVI 상태관리

화면의 상태를 누가 소유하고, 그 상태가 어떤 방향으로 흐르며, 사용자 입력은 어떻게 상태로 반영되는가. 이 질문에 답하는 설계 원칙이 **UDF(Unidirectional Data Flow, 단방향 데이터 흐름)**이고, 그 위에 세워진 두 패턴이 **MVVM**과 **MVI**입니다. 이 토픽은 단방향 흐름의 정의에서 출발해, 상태를 표현하는 `sealed` 계층, 상태와 일회성 이벤트의 분리, 그리고 두 패턴의 실제 차이를 다룹니다.

## 단방향 데이터 흐름(UDF) {#udf}

단방향 데이터 흐름은 **상태(state)는 한 방향으로만 아래로 흐르고, 이벤트(event)는 반대 방향으로만 위로 흐른다**는 원칙입니다. 안드로이드 화면 아키텍처에서 이 두 방향은 다음과 같습니다.

- **상태 하향(state down)**: ViewModel이 화면 상태를 만들어 UI(Composable, Activity, Fragment)로 내려보냅니다. UI는 받은 상태를 그대로 그리기만 합니다.
- **이벤트 상향(event up)**: UI에서 발생한 사용자 입력(클릭, 입력, 스크롤)은 ViewModel로 올라가고, ViewModel만이 그 이벤트를 받아 상태를 바꿉니다.

핵심은 **상태를 바꾸는 권한이 한 곳(ViewModel)에 집중된다**는 점입니다. UI는 상태를 직접 수정하지 않고, 오직 "이런 일이 일어났다"는 이벤트만 통지합니다.

```kotlin
// 상태는 ViewModel이 소유하고 읽기 전용으로 노출한다 (하향)
class CounterViewModel : ViewModel() {
    private val _count = MutableStateFlow(0)
    val count: StateFlow<Int> = _count.asStateFlow()   // 외부엔 읽기 전용

    fun onIncrement() {                                // 이벤트 수신 (상향)
        _count.update { it + 1 }                       // 상태 변경은 여기서만
    }
}
```

### 왜 단방향이어야 하는가 {#why-unidirectional}

양방향으로 상태를 변경할 수 있으면, 즉 UI도 ViewModel도 같은 상태를 직접 쓰면 다음 문제가 생깁니다.

1. **상태 출처가 불분명해진다**: 화면이 잘못 그려졌을 때 누가 상태를 바꿨는지 추적할 지점이 여러 곳으로 흩어집니다.
2. **경쟁 상태(race)가 발생한다**: 여러 경로가 동시에 같은 상태를 수정하면 마지막 쓰기가 이전 쓰기를 덮어쓰는 일이 생깁니다.
3. **테스트가 어려워진다**: 상태 변경 로직이 UI에 섞이면 ViewModel만 단위 테스트하는 것으로는 동작을 검증할 수 없습니다.

단방향은 이 셋을 **상태 변경 진입점을 ViewModel의 함수로 단일화**해서 해결합니다. 상태가 틀렸다면 원인은 항상 ViewModel 안에 있습니다.

## sealed UiState로 화면 상태 모델링 {#sealed-uistate}

화면 상태를 `Boolean` 플래그 여러 개로 표현하면 **모순된 조합**이 만들어질 수 있습니다. 예를 들어 `isLoading`, `error`, `data`를 따로 두면 `isLoading=true`이면서 `error != null`인, 실제로는 불가능해야 할 상태가 컴파일 단계에서 막히지 않습니다.

```kotlin
// 안티패턴: 서로 모순되는 상태가 표현 가능하다
data class BadUiState(
    val isLoading: Boolean = false,
    val data: List<Item>? = null,
    val error: String? = null,
)
// isLoading=true && error="..." 같은 불가능한 조합이 컴파일된다
```

`sealed interface`(또는 `sealed class`)로 모델링하면 **화면이 가질 수 있는 상태를 유한한 경우의 수로 닫아** 둡니다. 한 시점에 상태는 반드시 그 중 정확히 하나입니다.

```kotlin
sealed interface UiState {
    data object Loading : UiState
    data class Success(val items: List<Item>) : UiState
    data class Error(val message: String) : UiState
}
```

이렇게 하면 두 가지 이점이 생깁니다.

- **불가능한 상태가 표현 불가능해진다**: `Loading`이면서 동시에 `Error`인 값은 타입상 만들 수 없습니다.
- **`when`이 망라성(exhaustiveness)을 강제한다**: `sealed` 타입을 `when`으로 분기하면 컴파일러가 모든 경우를 다뤘는지 검사합니다. 상태를 새로 추가하면 처리하지 않은 분기가 컴파일 에러로 드러납니다.

```kotlin
@Composable
fun Screen(state: UiState) {
    when (state) {                       // else 없이도 망라성 보장
        UiState.Loading -> LoadingSpinner()
        is UiState.Success -> ItemList(state.items)
        is UiState.Error -> ErrorView(state.message)
    }
}
```

> 한편, 로딩·에러·콘텐츠가 **동시에 공존**할 수 있는 화면(예: 본문은 떠 있는데 새로고침 인디케이터가 같이 도는 화면)이라면 단일 `sealed`보다 `data class` 하나에 필드를 모으는 편이 맞습니다. `sealed`는 "정확히 하나"가 자연스러운 화면에, `data class`는 "여러 부분 상태가 공존"하는 화면에 적합합니다. 둘은 우열이 아니라 화면 성격에 따른 선택입니다.

## 상태와 일회성 이벤트의 분리 {#state-vs-event}

UDF에서 ViewModel이 UI로 내려보내는 것에는 성격이 다른 두 가지가 섞여 있습니다.

- **상태(state)**: 화면이 "현재 어떤 모습이어야 하는가". 구독 시점과 무관하게 항상 최신 값이 유효하며, 화면 회전 같은 재구독 후에도 다시 적용돼야 합니다. (예: 목록 데이터, 로딩 여부)
- **일회성 이벤트(one-off event / side effect)**: "지금 한 번 일어나야 하는 동작". 정확히 한 번만 소비돼야 합니다. (예: 스낵바 노출, 화면 이동, 토스트)

이 둘을 같은 `StateFlow`로 흘리면 문제가 생깁니다. `StateFlow`는 **최신 값을 보관**했다가 새 구독자에게 다시 방출하기 때문입니다. "회원가입 성공 → 화면 이동"을 상태로 흘리면, 화면 회전으로 재구독될 때 그 값이 다시 방출되어 **화면 이동이 한 번 더 일어나는** 버그가 됩니다.

### 일회성 이벤트의 올바른 전달 {#one-off-channel}

권장 방식은 일회성 이벤트를 상태와 분리해, **재방출되지 않는 채널**로 보내는 것입니다. 코루틴의 `Channel`을 `receiveAsFlow()`로 노출하면 각 이벤트는 정확히 한 소비자에게 한 번만 전달됩니다.

```kotlin
sealed interface UiState {
    data object Idle : UiState
    data object Loading : UiState
    data object Done : UiState
}

class SignUpViewModel : ViewModel() {
    private val _uiState = MutableStateFlow<UiState>(UiState.Idle)
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    // 일회성 이벤트는 상태와 별도 스트림으로
    private val _effect = Channel<Effect>(Channel.BUFFERED)
    val effect: Flow<Effect> = _effect.receiveAsFlow()  // 값을 보관하지 않음

    fun onSubmit() = viewModelScope.launch {
        _uiState.value = UiState.Loading
        runCatching { repo.signUp() }
            .onSuccess { _effect.send(Effect.NavigateToHome) }
            .onFailure { _effect.send(Effect.ShowSnackbar(it.message.orEmpty())) }
    }
}

sealed interface Effect {
    data object NavigateToHome : Effect
    data class ShowSnackbar(val message: String) : Effect
}
```

UI는 상태와 이벤트를 다르게 수집합니다. 상태는 `lifecycle`에 맞춰 계속 구독하고, 이벤트는 한 번씩 처리합니다.

```kotlin
// Compose에서: 이벤트는 한 번만 소비
LaunchedEffect(Unit) {
    viewModel.effect.collect { effect ->
        when (effect) {
            Effect.NavigateToHome -> navController.navigate("home")
            is Effect.ShowSnackbar -> snackbarHostState.showSnackbar(effect.message)
        }
    }
}
```

> `SharedFlow(replay = 0)`로도 일회성 이벤트를 표현하지만, 그 시점에 활성 구독자가 없으면 이벤트가 유실됩니다. `Channel`은 버퍼에 쌓아 두었다가 구독자가 생기면 전달하므로, 백그라운드로 갔다 돌아오는 화면에서 이벤트를 잃지 않으려면 `Channel` 쪽이 더 안전합니다.

## MVVM vs MVI {#mvvm-vs-mvi}

두 패턴 모두 UDF를 따르며 ViewModel이 상태를 소유합니다. 차이는 **상태를 몇 개로 쪼개 두는가**와 **상태 변경 진입점을 어떻게 정의하는가**에 있습니다.

### MVVM의 상태 노출 {#mvvm-state}

전통적 MVVM은 화면 상태를 **여러 개의 관찰 가능한 스트림**으로 나눠 노출하고, UI 이벤트마다 ViewModel에 **개별 함수**를 둡니다.

```kotlin
class ProfileViewModel : ViewModel() {
    val name: StateFlow<String> = ...
    val isLoading: StateFlow<Boolean> = ...
    val items: StateFlow<List<Item>> = ...

    fun onRefresh() { ... }          // 입력마다 개별 메서드
    fun onNameChange(v: String) { ... }
}
```

장점은 단순하고 직관적이라는 점입니다. 단점은 상태가 여러 스트림으로 흩어져, 앞서 본 **모순된 조합**이 생길 수 있고 "현재 화면 전체 상태"를 한눈에 보기 어렵다는 점입니다.

### MVI의 상태 노출 {#mvi-state}

MVI(Model-View-Intent)는 화면 상태를 **단 하나의 불변 객체(State)**로 합치고, 모든 사용자 입력을 **하나의 진입점(Intent)**으로 받습니다. Intent는 보통 `sealed` 타입으로 열거되며, ViewModel은 `(현재 State, Intent) → 새 State`로 상태를 갱신합니다.

```kotlin
data class ProfileState(
    val name: String = "",
    val isLoading: Boolean = false,
    val items: List<Item> = emptyList(),
)

sealed interface ProfileIntent {
    data object Refresh : ProfileIntent
    data class NameChanged(val value: String) : ProfileIntent
}

class ProfileViewModel : ViewModel() {
    private val _state = MutableStateFlow(ProfileState())
    val state: StateFlow<ProfileState> = _state.asStateFlow()

    fun onIntent(intent: ProfileIntent) = when (intent) {   // 단일 진입점
        ProfileIntent.Refresh -> reduce { copy(isLoading = true) }
        is ProfileIntent.NameChanged -> reduce { copy(name = intent.value) }
    }

    private fun reduce(block: ProfileState.() -> ProfileState) {
        _state.update(block)
    }
}
```

MVI의 핵심 성질은 다음과 같습니다.

- **단일 상태(single source of truth)**: 화면 전체 상태가 하나의 불변 객체이므로, 그 객체만 보면 화면을 완전히 재현할 수 있습니다.
- **단일 진입점(intent)**: 모든 입력이 `onIntent` 한 곳을 지나므로 로깅·디버깅·상태 전이 추적이 한 지점에 모입니다.
- **불변 상태 + 환원(reduce)**: 상태를 직접 수정하지 않고 `copy`로 새 상태를 만들어 교체합니다. 변경 이력을 다루기 쉽습니다.

### 무엇을 언제 쓰는가 {#mvvm-mvi-choice}

| 구분 | MVVM | MVI |
|------|------|-----|
| 화면 상태 | 여러 스트림으로 분리 | 단일 불변 State 객체 |
| 입력 진입점 | 입력마다 개별 메서드 | `onIntent` 단일 진입점 |
| 상태 변경 | 각 스트림을 개별 갱신 | reduce로 새 State 생성·교체 |
| 모순 상태 | 발생 가능 | 단일 객체라 통제 쉬움 |
| 보일러플레이트 | 적음 | 상대적으로 많음 |
| 적합한 화면 | 상태가 단순한 화면 | 상태 전이가 복잡한 화면 |

MVI가 더 엄격하지만, 그만큼 코드가 늘어납니다. **둘은 대립 관계가 아니라 같은 UDF 위의 정도 차이**입니다. 실무에서는 단순 화면은 MVVM처럼 가볍게, 상태 전이가 복잡한 화면은 MVI처럼 단일 State + Intent로 가는 혼합이 흔합니다. 두 패턴 모두 일회성 이벤트는 앞서 본 대로 상태와 분리해 처리하는 것이 공통 원칙입니다.

## 요약 {#summary}

> **TL;DR** — UDF는 상태를 ViewModel에서 UI로 아래로만 흘리고, 이벤트를 위로만 올려 상태 변경 권한을 한 곳에 모으는 원칙입니다. 화면 상태는 `sealed UiState`로 모델링해 불가능한 조합을 타입으로 막고 `when` 망라성을 얻습니다. 회전 후 재방출되면 안 되는 일회성 이벤트(내비게이션·스낵바)는 상태와 분리해 `Channel`로 보냅니다. MVVM과 MVI는 모두 UDF를 따르되, MVI는 상태를 단일 불변 객체로 합치고 입력을 단일 Intent로 받는다는 점에서 더 엄격합니다.

1. **단방향 데이터 흐름(UDF)**: 상태는 ViewModel→UI로 하향, 이벤트는 UI→ViewModel로 상향. 상태 변경 진입점을 ViewModel로 단일화해 추적성·테스트성을 확보한다.
2. **sealed UiState**: 화면 상태를 유한한 경우로 닫아 모순된 조합을 타입으로 막고, `when` 망라성으로 누락을 컴파일 단계에서 잡는다.
3. **상태·이벤트 분리**: 보관·재방출되는 상태(`StateFlow`)와 한 번만 소비돼야 하는 일회성 이벤트(`Channel`)를 분리해, 화면 회전 시 내비게이션이 재실행되는 버그를 막는다.
4. **MVVM vs MVI**: 둘 다 UDF 기반. MVVM은 상태를 여러 스트림+개별 메서드로, MVI는 단일 불변 State+단일 Intent로 다룬다. 우열이 아니라 화면 복잡도에 따른 선택이다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 단방향 데이터 흐름(UDF)이 무엇이고, 양방향 대비 어떤 문제를 해결하나요?">

UDF는 상태는 ViewModel에서 UI로 한 방향으로만 내려가고, 사용자 입력 이벤트는 UI에서 ViewModel로 한 방향으로만 올라가는 원칙입니다. 핵심은 상태를 변경하는 권한이 ViewModel 한 곳에 집중된다는 점입니다. UI는 상태를 직접 수정하지 않고, 이벤트만 통지합니다.

양방향으로 상태를 수정할 수 있으면 상태를 누가 바꿨는지 출처가 흩어져 추적이 어렵고, 여러 경로가 동시에 같은 상태를 써서 경쟁 상태가 생기며, 상태 변경 로직이 UI에 섞여 테스트가 어려워집니다. UDF는 상태 변경 진입점을 ViewModel의 함수로 단일화해 이 셋을 막습니다. 화면이 잘못 그려졌다면 원인은 항상 ViewModel 안에 있습니다.

</def>
<def title="Q) 화면 상태를 sealed 타입으로 모델링하면 Boolean 플래그 방식 대비 무엇이 좋아지나요?">

`isLoading`, `error`, `data`를 각각 따로 두면 `isLoading=true`이면서 `error != null`인, 실제로는 불가능해야 할 조합이 컴파일 단계에서 막히지 않습니다. `sealed interface`로 `Loading`, `Success(data)`, `Error(message)`처럼 모델링하면 한 시점에 상태는 반드시 그 중 하나가 되어, 불가능한 조합 자체를 타입으로 표현할 수 없게 됩니다.

또한 `sealed` 타입을 `when`으로 분기하면 컴파일러가 모든 경우를 다뤘는지 망라성을 검사합니다. 상태를 새로 추가하면 처리하지 않은 분기가 컴파일 에러로 드러나, 누락을 런타임이 아니라 빌드 시점에 잡을 수 있습니다. 단, 로딩·에러·콘텐츠가 동시에 공존해야 하는 화면이라면 단일 sealed보다 data class에 필드를 모으는 편이 적합합니다.

</def>
<def title="Q) 화면 회전 후 스낵바나 내비게이션이 중복 실행되는 버그는 왜 생기고, 어떻게 막나요?">

내비게이션·스낵바 같은 일회성 이벤트를 `StateFlow`에 담았기 때문입니다. `StateFlow`는 최신 값을 보관했다가 새 구독자에게 다시 방출하므로, 화면 회전으로 재구독되면 직전 이벤트 값이 다시 흘러 화면 이동이나 스낵바가 한 번 더 실행됩니다.

해결책은 상태와 일회성 이벤트를 분리하는 것입니다. 상태는 보관·재방출이 정상이지만, 일회성 이벤트는 정확히 한 번만 소비돼야 하므로 값을 보관하지 않는 스트림으로 보냅니다. 코루틴 `Channel`을 `receiveAsFlow()`로 노출하면 각 이벤트가 한 소비자에게 한 번만 전달됩니다. `SharedFlow(replay=0)`도 가능하지만 그 시점에 구독자가 없으면 이벤트가 유실되므로, 백그라운드 복귀 시에도 잃지 않으려면 버퍼링되는 `Channel`이 더 안전합니다.

</def>
<def title="Q) MVVM과 MVI의 차이는 무엇이고, 언제 어느 쪽을 선택하나요?">

둘 다 UDF를 따르고 ViewModel이 상태를 소유한다는 점은 같습니다. 차이는 상태를 어떻게 묶고 입력을 어떻게 받는가입니다. MVVM은 화면 상태를 여러 개의 관찰 가능한 스트림으로 나눠 노출하고, 사용자 입력마다 개별 메서드를 둡니다. 단순하지만 상태가 흩어져 모순된 조합이 생길 수 있습니다.

MVI는 화면 상태를 단 하나의 불변 객체로 합치고, 모든 입력을 단일 진입점(`onIntent`)으로 받아 `(현재 State, Intent) → 새 State`로 갱신합니다. 단일 상태라 화면을 한 객체로 재현할 수 있고, 모든 입력이 한 지점을 지나 디버깅·로깅이 모이지만 보일러플레이트가 늘어납니다. 우열 관계가 아니라 정도 차이이므로, 상태가 단순한 화면은 MVVM처럼 가볍게, 상태 전이가 복잡한 화면은 MVI처럼 단일 State와 Intent로 가는 혼합이 실무에서 흔합니다.

</def>
</deflist>

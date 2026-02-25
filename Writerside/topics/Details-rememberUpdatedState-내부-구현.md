# Details: rememberUpdatedState 내부 구현

## rememberUpdatedState는 내부적으로 어떻게 구현되어 있나요? {#rememberupdatedstate-internals}

`rememberUpdatedState`의 동작 방식은 처음에는 복잡해 보일 수 있지만, 내부 구현은 놀랍도록 단순합니다. 그 구현을 직접 살펴보면 동작 원리를 명확히 이해할 수 있습니다.

### 내부 구현 코드 {#internal-implementation}

```kotlin
@Composable
fun <T> rememberUpdatedState(newValue: T): State<T> =
    remember { mutableStateOf(newValue) }.apply { value = newValue }
```
{title="rememberUpdatedState.kt"}

### 동작 원리 분석 {#how-it-works-internally}

`rememberUpdatedState`의 구현은 두 가지 핵심 동작으로 구성됩니다.

**1. `remember { mutableStateOf(newValue) }`**

`remember`를 사용하여 `MutableState<T>` 객체를 최초 Composition 시 한 번만 생성하고 기억합니다. 이 객체는 리컴포지션이 발생해도 새로 생성되지 않고 동일한 인스턴스가 유지됩니다.

**2. `.apply { value = newValue }`**

`apply` 스코프 함수를 통해 리컴포지션마다 기억된 `MutableState`의 `value`를 최신 `newValue`로 갱신합니다. Composable 함수가 리컴포지션될 때마다 `rememberUpdatedState`가 호출되고, 이때 이전에 기억된 상태가 새로운 값으로 업데이트됩니다.

```kotlin
// 직접 구현하면 다음과 동일한 동작을 합니다
@Composable
fun <T> rememberUpdatedStateEquivalent(newValue: T): State<T> {
    val state = remember { mutableStateOf(newValue) }
    state.value = newValue  // 매 리컴포지션마다 최신 값으로 갱신
    return state
}
```
{title="RememberUpdatedStateEquivalent.kt"}

### `remember`만 사용했을 때와의 차이 {#difference-from-plain-remember}

단순히 `remember { mutableStateOf(newValue) }`만 사용하면 초기값만 기억되고 이후 `newValue`가 변경되어도 상태가 갱신되지 않습니다. `rememberUpdatedState`는 여기에 `.apply { value = newValue }`를 추가하여 리컴포지션마다 값을 동기화합니다.

```kotlin
@Composable
fun Example(callback: () -> Unit) {
    // 잘못된 방법: 초기 callback만 기억되고 이후 변경 사항이 반영되지 않음
    val staleCallback = remember { mutableStateOf(callback) }

    // 올바른 방법: 리컴포지션마다 최신 callback으로 갱신됨
    val currentCallback by rememberUpdatedState(callback)
}
```
{title="ComparisonExample.kt"}

### 요약 {#summary}

<tldr>
`rememberUpdatedState`는 `remember { mutableStateOf(newValue) }.apply { value = newValue }` 한 줄로 구현됩니다. `remember`로 상태 객체를 한 번만 생성하고, `apply`를 통해 매 리컴포지션마다 최신 값으로 갱신하는 단순하면서도 강력한 패턴입니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) rememberUpdatedState를 직접 구현한다면 어떻게 작성할 수 있나요?">

내부 구현을 이해하면 동일한 동작을 직접 작성할 수 있습니다.

```kotlin
@Composable
fun <T> myRememberUpdatedState(newValue: T): State<T> {
    // 1. 최초 Composition 시 MutableState 생성 (이후 리컴포지션에서는 재사용)
    val state = remember { mutableStateOf(newValue) }
    // 2. 매 리컴포지션마다 최신 값으로 갱신
    state.value = newValue
    return state
}
```
{title="MyRememberUpdatedState.kt"}

이는 공식 구현인 `remember { mutableStateOf(newValue) }.apply { value = newValue }`와 완전히 동일하게 동작합니다. 핵심은 `remember`로 상태 인스턴스의 수명을 Composition에 연결하면서, 동시에 매 리컴포지션마다 값을 갱신하는 것입니다.

</def>
</deflist>

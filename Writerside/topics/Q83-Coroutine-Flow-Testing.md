# Q83) 코루틴·Flow 테스트

코루틴과 Flow는 비동기·시간 의존 코드입니다. 그래서 일반적인 동기 테스트처럼 작성하면 두 가지 문제가 생깁니다. 첫째, suspend 함수를 테스트 함수에서 직접 호출할 수 없습니다. 둘째, `delay`나 타이머가 들어간 코드를 실제 시간으로 기다리면 테스트가 느리고 불안정(flaky)해집니다.

이 토픽은 이 두 문제를 해결하는 표준 도구인 `kotlinx-coroutines-test` 라이브러리와 Flow 검증 라이브러리 Turbine을 다룹니다. 핵심은 **실제 시간을 가상 시간으로 대체해 결정론적(deterministic)으로 만든다**는 것입니다.

## 가상 시간과 TestDispatcher {#virtual-time-dispatcher}

### 가상 시간이란 {#what-is-virtual-time}

`TestDispatcher`는 **가상 시간(virtual time)** 을 사용하는 디스패처입니다. 가상 시간은 실제 시계가 아니라, 스케줄러가 관리하는 논리적 시간 카운터입니다. 코루틴이 `delay(1000)`을 호출해도 실제로 1초를 기다리지 않고, 가상 시계의 눈금만 1000ms 앞으로 당겨질 뿐입니다.

이 덕분에 얻는 것이 두 가지입니다.

1. **속도**: `delay(10_000)`이 있는 코드도 즉시 통과합니다. 실제로 10초를 기다리지 않습니다.
2. **결정론**: 어떤 코루틴이 언제 실행되는지가 스케줄러에 의해 정해지므로, 실행 순서가 매번 동일합니다. 실제 스레드 스케줄링의 비결정성이 사라집니다.

### TestDispatcher의 두 종류 {#two-test-dispatchers}

`TestDispatcher`에는 같은 `TestCoroutineScheduler`를 공유하는 두 구현체가 있습니다. 차이는 **새로 시작된 코루틴을 즉시 실행하는가**입니다.

- **`StandardTestDispatcher`**: 새 코루틴을 즉시 실행하지 않고 스케줄러 큐에 넣어 둡니다. 실행하려면 `advanceUntilIdle()`, `runCurrent()`, `advanceTimeBy()` 등으로 직접 시간을 진행시켜야 합니다. 코루틴들의 실행 순서를 세밀하게 제어해 검증하고 싶을 때 적합합니다.
- **`UnconfinedTestDispatcher`**: 새 코루틴을 시작 즉시 첫 suspend 지점까지 동기적으로 실행합니다. 디스패치를 기다릴 필요 없이 곧바로 결과를 볼 수 있어 간단한 테스트에 편리하지만, 실행 순서가 직관과 달라질 수 있습니다.

```kotlin
// 스케줄러를 공유하면 두 디스패처가 같은 가상 시계를 사용한다
val scheduler = TestCoroutineScheduler()
val standard = StandardTestDispatcher(scheduler)
val unconfined = UnconfinedTestDispatcher(scheduler)
```

`runTest`는 인자를 주지 않으면 기본으로 `StandardTestDispatcher`를 사용합니다. 즉 기본 동작은 "코루틴이 자동 실행되지 않으니 시간을 직접 진행시켜라"입니다.

## runTest {#runtest}

### runTest의 역할 {#runtest-role}

`runTest`는 **코루틴 테스트의 진입점**입니다. suspend 람다를 받아 `TestScope` 안에서 실행하며, 다음을 자동으로 처리합니다.

- 테스트 본문을 코루틴으로 실행해 그 안에서 suspend 함수를 직접 호출할 수 있게 합니다.
- 본문에서 시작된 자식 코루틴이 모두 끝날 때까지 기다린 뒤 종료합니다. 본문이 끝나면 스케줄러가 idle 상태가 될 때까지 가상 시간을 진행시켜 줍니다. 이 동작을 흔히 **자동 advance**라고 부르는데, 공식 문서 용어가 아니라 설명을 위한 명칭입니다.
- 실제 시간 기준 타임아웃(기본 60초)을 걸어, 코루틴이 영원히 끝나지 않는 경우 테스트가 실패하도록 합니다.

```kotlin
@Test
fun loadUser_returnsUser() = runTest {
    val repository = UserRepository(api = FakeApi())
    val user = repository.loadUser()   // suspend 함수를 직접 호출
    assertEquals("ckgod", user.name)
}
```

`runTest`는 `runBlocking`과 다릅니다. `runBlocking`은 실제 시간으로 블로킹하므로 `delay`가 실제로 대기하지만, `runTest`는 가상 시간을 쓰므로 `delay`를 즉시 건너뜁니다.

### runTest 안에서의 시간 제어 {#time-control-in-runtest}

`runTest`의 람다 리시버는 `TestScope`이며, 여기서 스케줄러 제어 함수들을 호출할 수 있습니다.

```kotlin
@Test
fun delayedWork() = runTest {
    var done = false
    launch {
        delay(5_000)
        done = true
    }

    assertFalse(done)        // 아직 launch 본문이 delay에서 멈춰 있다
    advanceTimeBy(5_000)     // 가상 시간을 5초 진행
    runCurrent()             // 5000ms 시점에 예약된 작업을 실행
    assertTrue(done)
}
```

- `advanceTimeBy(ms)`: 가상 시간을 지정한 만큼 진행시키고, 그 사이에 예약된 작업을 실행합니다. 다만 정확히 그 시각에 예약된 작업은 실행하지 않으므로, 경계 시점 작업까지 실행하려면 뒤에 `runCurrent()`를 붙입니다. 위 예시는 같은 효과를 `advanceTimeBy(5_001)`처럼 경계 너머로 한 틱 더 진행시키거나, 남은 작업이 이것뿐이라면 `advanceUntilIdle()`로도 얻을 수 있습니다.
- `runCurrent()`: 현재 가상 시간에 이미 예약된 작업만 실행하고 시간은 진행시키지 않습니다.

## advanceUntilIdle {#advance-until-idle}

### 동작 정의 {#advance-until-idle-behavior}

`advanceUntilIdle()`은 **스케줄러에 예약된 모든 작업이 없어질 때까지 가상 시간을 끝까지 진행시키는** 함수입니다. 큐에 남은 코루틴과 예약된 `delay`를 전부 소진합니다.

`StandardTestDispatcher`는 코루틴을 자동 실행하지 않기 때문에, 시작만 해 둔 코루틴의 결과를 확인하려면 `advanceUntilIdle()`로 명시적으로 실행을 끝내 줘야 합니다.

```kotlin
@Test
fun fetchAndStore() = runTest {
    val repo = Repository(api = FakeApi())

    repo.refresh()           // 내부에서 launch로 비동기 작업 시작
    // 이 시점에는 StandardTestDispatcher라 아직 실행되지 않았을 수 있다

    advanceUntilIdle()       // 모든 예약 작업을 끝까지 실행
    assertEquals(3, repo.cache.size)
}
```

### advanceUntilIdle vs advanceTimeBy {#advance-comparison}

| 함수 | 진행 범위 | 쓰는 상황 |
|------|-----------|-----------|
| `advanceUntilIdle()` | 더 이상 할 일이 없을 때까지 끝까지 | 작업 완료 후의 최종 결과만 확인 |
| `advanceTimeBy(ms)` | 지정한 가상 시간만큼만 | 특정 시점의 중간 상태를 검증 |
| `runCurrent()` | 시간 진행 없이 현재 예약분만 | 경계 시점 작업 실행, 미세 제어 |

주의할 점은 무한 루프입니다. `while(true) { delay(1000) }`처럼 끝나지 않는 코루틴이 큐에 있으면 `advanceUntilIdle()`은 영원히 진행하려다 멈추지 않습니다. 이런 코드(예: 무한히 도는 Hot Flow 수집)는 `advanceUntilIdle()` 대신 `advanceTimeBy()`로 필요한 만큼만 진행시키거나, 별도 스코프에서 수집 Job을 만들고 마지막에 `cancel()`해야 합니다.

## Turbine으로 Flow 테스트 {#turbine}

### 왜 Turbine인가 {#why-turbine}

Flow를 테스트할 때 `toList()`로 전부 모으는 방법은 **무한 Flow나 Hot Flow(StateFlow/SharedFlow)에는 쓸 수 없습니다.** `toList()`는 Flow가 완료(complete)돼야 반환되는데, StateFlow는 절대 완료되지 않기 때문입니다. 수동으로 `launch`해서 수집 리스트를 만들고 마지막에 취소하는 코드는 장황하고 실수가 잦습니다.

[Turbine](https://github.com/cashapp/turbine)은 이 패턴을 캡슐화한 라이브러리입니다. `test { }` 블록 안에서 방출을 **하나씩 순서대로 소비**하면서 검증하고, 검증이 끝나면 자동으로 수집을 취소합니다. 무한·Hot Flow뿐 아니라 정상 완료되는 유한 Cold Flow에서도 방출을 순서대로 검증할 수 있어 권장됩니다.

### 기본 사용법 {#turbine-basics}

```kotlin
@Test
fun emitsItemsInOrder() = runTest {
    flowOf(1, 2, 3).test {
        assertEquals(1, awaitItem())
        assertEquals(2, awaitItem())
        assertEquals(3, awaitItem())
        awaitComplete()          // Flow가 정상 종료됐음을 검증
    }
}
```

주요 함수는 다음과 같습니다.

- `awaitItem()`: 다음 방출 값을 기다려 반환합니다. 일정 시간 안에 값이 없으면 실패합니다.
- `awaitComplete()`: Flow가 정상 완료됐는지 검증합니다.
- `awaitError()`: Flow가 예외로 종료됐는지 검증하고 그 예외를 반환합니다.
- `expectNoEvents()`: 현재 시점에 대기 중인 이벤트가 없는지 확인합니다.
- `cancelAndIgnoreRemainingEvents()`: 남은 방출을 무시하고 수집을 끝냅니다. 무한·Hot Flow에서 마무리할 때 씁니다.

### StateFlow 테스트 {#turbine-stateflow}

StateFlow는 완료되지 않으므로 Turbine이 특히 유용합니다. StateFlow를 구독하면 **현재 값을 먼저 한 번 받는다**는 점을 기억해야 합니다. 따라서 첫 `awaitItem()`은 초기값입니다.

```kotlin
@Test
fun uiState_movesToSuccess() = runTest {
    val viewModel = NewsViewModel(repository = FakeRepository())

    viewModel.uiState.test {
        assertEquals(UiState.Loading, awaitItem())   // 초기값
        viewModel.load()
        advanceUntilIdle()                           // 로딩 코루틴 완료시킴
        assertEquals(UiState.Success(news), awaitItem())
        cancelAndIgnoreRemainingEvents()             // StateFlow는 안 끝나므로 직접 종료
    }
}
```

여기서 `runTest`의 가상 시간 제어(`advanceUntilIdle`)와 Turbine의 방출 검증이 함께 쓰이는 것이 전형적인 ViewModel 테스트 형태입니다.

## 디스패처 주입과 Main 교체 {#dispatcher-injection}

테스트가 결정론적이려면, 프로덕션 코드가 `Dispatchers.IO`나 `Dispatchers.Default`를 **하드코딩하지 않고 주입받아야** 합니다. 그래야 테스트에서 `TestDispatcher`로 갈아끼울 수 있습니다.

```kotlin
class UserRepository(
    private val api: Api,
    private val dispatcher: CoroutineDispatcher = Dispatchers.IO  // 주입 가능하게
) {
    suspend fun loadUser(): User = withContext(dispatcher) {
        api.fetchUser()
    }
}

// 테스트
@Test
fun loadUser() = runTest {
    val repo = UserRepository(FakeApi(), dispatcher = StandardTestDispatcher(testScheduler))
    // testScheduler를 공유해야 가상 시간이 일관된다
    val user = repo.loadUser()
    assertNotNull(user)
}
```

`viewModelScope`나 `Dispatchers.Main`을 내부에서 직접 쓰는 코드는 주입이 어렵습니다. 이때는 `Dispatchers.setMain(testDispatcher)`로 전역 Main 디스패처를 테스트용으로 교체하고, 테스트가 끝나면 `Dispatchers.resetMain()`으로 되돌립니다.

```kotlin
@Before
fun setUp() {
    Dispatchers.setMain(StandardTestDispatcher())
}

@After
fun tearDown() {
    Dispatchers.resetMain()
}
```

## 요약 {#summary}

> **TL;DR** — 코루틴·Flow 테스트의 핵심은 실제 시간을 `TestDispatcher`의 가상 시간으로 바꿔 빠르고 결정론적으로 만드는 것입니다. `runTest`가 진입점이 되어 suspend 함수를 직접 호출하고 자동으로 시간을 끝까지 진행시키며, 세밀한 제어가 필요하면 `advanceUntilIdle`·`advanceTimeBy`·`runCurrent`로 가상 시계를 직접 움직입니다. Flow 방출 검증은 Turbine의 `test { awaitItem() }`으로 StateFlow를 포함한 모든 Flow를 안전하게 한 값씩 확인합니다. 프로덕션 코드는 디스패처를 주입받거나 `Dispatchers.setMain`으로 교체해야 테스트가 가상 시간 위에서 동작합니다.

1. **가상 시간과 TestDispatcher**: `TestDispatcher`는 실제 시계 대신 스케줄러의 논리적 시간을 쓴다. `delay`가 즉시 건너뛰어져 빠르고, 실행 순서가 고정돼 결정론적이다. `StandardTestDispatcher`(수동 진행)와 `UnconfinedTestDispatcher`(즉시 실행)가 있다.
2. **runTest**: 코루틴 테스트의 진입점. suspend 본문을 `TestScope`에서 실행하고, 본문이 시작한 자식 코루틴을 끝까지 자동 advance한다. `runBlocking`과 달리 가상 시간을 쓴다.
3. **advanceUntilIdle**: 예약된 작업이 모두 없어질 때까지 가상 시간을 끝까지 진행. `StandardTestDispatcher`에서 시작만 해 둔 코루틴의 결과를 확인할 때 필수. 무한 코루틴에는 쓰면 안 된다.
4. **Turbine**: `test { }` 안에서 `awaitItem()`으로 방출을 하나씩 검증하고 자동 취소한다. `toList()`로 못 다루는 무한·Hot Flow(StateFlow/SharedFlow) 테스트의 표준 도구다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) TestDispatcher의 가상 시간이 무엇이고, 일반 테스트 대비 어떤 이점을 주나요?">

가상 시간은 실제 시계가 아니라 `TestCoroutineScheduler`가 관리하는 논리적 시간 카운터입니다. 코루틴이 `delay(1000)`을 호출해도 실제로 1초를 기다리지 않고 가상 시계 눈금만 1000ms 앞으로 당겨집니다.

이점은 두 가지입니다. 첫째, 속도입니다. `delay(10_000)`이 들어간 코드도 실제로 기다리지 않고 즉시 통과하므로 테스트가 빠릅니다. 둘째, 결정론입니다. 어떤 코루틴이 언제 실행되는지를 스케줄러가 결정하므로 실행 순서가 매번 같고, 실제 스레드 스케줄링의 비결정성에서 오는 flaky 테스트가 사라집니다. 이 가상 시간을 쓰는 디스패처가 `TestDispatcher`이며, 자동 실행하지 않는 `StandardTestDispatcher`와 즉시 실행하는 `UnconfinedTestDispatcher` 두 종류가 있습니다.

</def>
<def title="Q) runTest와 runBlocking의 차이는 무엇인가요? runTest는 어떤 일을 자동으로 해 주나요?">

가장 큰 차이는 시간 처리입니다. `runBlocking`은 실제 시간으로 스레드를 블로킹하므로 `delay(5000)`이 실제로 5초를 대기합니다. 반면 `runTest`는 가상 시간을 쓰는 `TestScope`에서 본문을 실행하므로 `delay`를 즉시 건너뜁니다.

`runTest`가 자동으로 해 주는 일은 다음과 같습니다. 본문을 코루틴으로 실행해 그 안에서 suspend 함수를 직접 호출할 수 있게 하고, 본문이 시작한 자식 코루틴이 모두 끝날 때까지 가상 시간을 진행시킨 뒤(자동 advance) 종료합니다. 또 코루틴이 끝나지 않는 경우를 잡기 위해 실제 시간 기준 기본 60초 타임아웃을 겁니다. 인자를 주지 않으면 기본으로 `StandardTestDispatcher`를 사용합니다.

</def>
<def title="Q) advanceUntilIdle, advanceTimeBy, runCurrent는 각각 언제 쓰나요?">

세 함수 모두 가상 시계를 제어하지만 진행 범위가 다릅니다.

`advanceUntilIdle()`은 스케줄러에 예약된 작업이 하나도 남지 않을 때까지 끝까지 진행시킵니다. `StandardTestDispatcher`에서 시작만 해 둔 코루틴을 모두 끝내고 최종 결과만 확인하고 싶을 때 씁니다. `advanceTimeBy(ms)`는 지정한 가상 시간만큼만 진행시켜, 특정 시점의 중간 상태를 검증할 때 씁니다. `runCurrent()`는 시간을 진행시키지 않고 현재 가상 시각에 이미 예약된 작업만 실행해, 경계 시점 작업 실행이나 미세 제어에 씁니다.

주의할 점은 무한 코루틴입니다. `while(true){ delay(...) }`처럼 끝나지 않는 작업이 큐에 있으면 `advanceUntilIdle()`은 멈추지 않으므로, 이때는 `advanceTimeBy()`로 필요한 만큼만 진행시키거나 수집 Job을 만들어 마지막에 `cancel()`해야 합니다.

</def>
<def title="Q) StateFlow를 테스트할 때 toList()를 쓰면 안 되는 이유와 Turbine으로 어떻게 해결하는지 설명해 주세요.">

`toList()`는 Flow가 완료(complete)돼야 반환됩니다. 그런데 StateFlow나 SharedFlow 같은 Hot Flow는 절대 완료되지 않으므로, `toList()`는 영원히 반환되지 않아 테스트가 멈춰 버립니다.

Turbine은 `flow.test { }` 블록 안에서 방출을 하나씩 소비하며 검증하고, 블록이 끝나면 수집을 자동으로 취소합니다. `awaitItem()`으로 다음 값을 받아 검증하고, 완료는 `awaitComplete()`, 예외는 `awaitError()`로 확인합니다. StateFlow는 구독 즉시 현재 값을 한 번 내보내므로 첫 `awaitItem()`은 초기값이라는 점을 기억해야 하고, 절대 끝나지 않으므로 검증이 끝나면 `cancelAndIgnoreRemainingEvents()`로 직접 마무리합니다. 보통 ViewModel 테스트에서는 `runTest`의 `advanceUntilIdle()`로 상태 변경 코루틴을 완료시킨 뒤, 다음 `awaitItem()`으로 바뀐 상태를 검증하는 방식으로 함께 씁니다.

</def>
<def title="Q) 테스트를 결정론적으로 만들려면 프로덕션 코드에서 디스패처를 어떻게 다뤄야 하나요?">

프로덕션 코드가 `Dispatchers.IO`나 `Dispatchers.Default`를 하드코딩하면 테스트에서 가상 시간으로 갈아끼울 수 없습니다. 따라서 디스패처를 생성자 등으로 주입받게 만들어, 테스트에서는 같은 `testScheduler`를 공유하는 `TestDispatcher`를 넣어야 합니다. 스케줄러를 공유해야 가상 시계가 하나로 일관되게 동작합니다.

`viewModelScope`나 `Dispatchers.Main`을 내부에서 직접 쓰는 코드처럼 주입이 어려운 경우에는, 테스트의 `@Before`에서 `Dispatchers.setMain(testDispatcher)`로 전역 Main 디스패처를 교체하고 `@After`에서 `Dispatchers.resetMain()`으로 되돌립니다. 이렇게 해야 Main 위에서 도는 코루틴도 가상 시간 위에서 결정론적으로 실행됩니다.

</def>
</deflist>

# Q18) snapshotFlow

## snapshotFlow는 무엇이고 어떻게 동작하나요? {#what-is-snapshotflow}

[snapshotFlow](https://developer.android.com/develop/ui/compose/side-effects#snapshotFlow)는 Compose의 State를 코틀린 Flow로 변환해 주는 함수입니다. Compose 내부에서 상태 변화를 효율적으로 관리·관찰하기 위해 사용하는 **Snapshot 시스템** 의 변경을 관찰하고, 관찰 대상 상태가 바뀔 때마다 갱신된 값을 Flow로 흘려보냅니다.

요약하자면 snapshotFlow는 Compose의 상태 변화를 Flow로 노출시켜, 표준 코루틴 기반 연산자로 상태 갱신에 반응할 수 있게 해 주는 다리 역할입니다.

### snapshotFlow의 핵심 특성 {#key-characteristics}

- **State 관찰**: Snapshot 시스템을 통해 Compose의 상태 변화를 감지합니다.
- **Thread Safety**: 상태 읽기와 emission이 Compose의 snapshot isolation 안에서 이뤄지므로 race condition을 피할 수 있습니다.
- **Idle Skipping**: 값이 실제로 바뀐 경우에만 emission이 발생하며, idle한 리컴포지션 동안에는 갱신을 흘리지 않습니다.
- **취소 인지(Cancelation-Aware)**: Flow를 수집하던 코루틴이 취소되면 관찰도 자동으로 종료되어, 컴포지션과 자연스럽게 묶여 동작합니다.

### snapshotFlow를 언제 쓰면 좋은가 {#when-to-use}

- **코루틴과의 연결**: 변환·결합·throttling 같은 코루틴 기반 연산이 필요할 때, Compose State를 Flow로 끌어와 처리하기에 좋습니다.
- **UI 외 부수 효과**: 분석 이벤트 전송이나 백엔드 호출처럼 UI에 직접 묶이지 않는 작업을 트리거할 때 유용합니다.

### 사용 예시 {#how-to-use}

리스트 스크롤에 따른 페이지네이션 처리가 대표적인 예입니다. snapshotFlow를 활용하면 정말 필요한 시점에만 다음 페이지를 불러올 수 있고, `shouldLoadMore` 가 true일 때만 요청이 발생하도록 제어할 수 있어 동일 항목에 대한 중복 요청을 막을 수 있습니다.

```kotlin
val listState = rememberLazyListState()
val threshold = 2

LazyColumn(state = listState) {
    // ... items ...
}

// 현재 ViewModel 의 로딩 상태를 관찰합니다.
val isLoadingShorts by shortsViewModel.isLoadingShorts.collectAsStateWithLifecycle()

// 페이지네이션을 위해 추가 로딩이 필요한지 판단합니다.
val shouldLoadMore by remember {
    derivedStateOf {
        val totalItemsCount = listState.layoutInfo.totalItemsCount
        val lastVisibleItemIndex =
            listState.layoutInfo.visibleItemsInfo.lastOrNull()?.index ?: 0
        (lastVisibleItemIndex + threshold >= totalItemsCount) && !isLoadingShorts
    }
}

// listState 가 바뀔 때마다 다시 시작합니다.
LaunchedEffect(listState) {
    snapshotFlow { shouldLoadMore } // 'shouldLoadMore' 변화를 관찰
        .map { shouldLoad -> shouldLoad } // 로딩 조건으로 매핑
        .distinctUntilChanged() // 실제 변경된 경우에만 emit
        .filter { it } // 'shouldLoadMore' 가 true 일 때만 진행
        .collect {
            // 추가 항목 로딩 이벤트를 트리거합니다.
            shortsViewModel.handleShortsEvent(event = ShortsEvent.LoadMore)
        }
}
```
{title="SnapshotFlowExample.kt"}

이 예시는 `LazyColumn` 의 스크롤 상태를 snapshotFlow로 관찰하다가, 마지막 항목이 임계치 안쪽으로 들어오면 추가 항목 로딩 이벤트를 한 번만 트리거합니다. `map`, `distinctUntilChanged`, `filter` 같은 연산자로 정말 필요한 시점에만 이벤트가 발사되도록 다듬는 것이 핵심입니다.

### snapshotFlow의 내부 동작 {#how-it-works-internally}

1. 전달된 람다를 Snapshot observer 안에서 평가합니다.
2. 람다 안에서 어떤 상태 변수에 접근하면 Compose는 그 상태에 대한 의존성을 등록합니다.
3. 의존성에 등록된 상태가 바뀌면 Compose가 snapshotFlow에 알리고, snapshotFlow가 새 값을 emit 합니다.

### 사용 시 유의할 점 {#things-to-keep-in-mind}

- **Thread Safety와 수집 범위**: Flow 수집은 반드시 코루틴 스코프 안(보통 `LaunchedEffect`)에서 이뤄져야 하며, 컴포지션 바깥에서 수집되어 메모리 누수가 생기지 않도록 주의해야 합니다.
- **Emission 빈도**: 람다 안에서 읽는 snapshot state가 바뀔 때마다 emission이 발생할 수 있어 빈도가 높아질 수 있습니다. `distinctUntilChanged()`, `debounce()` 같은 연산자를 활용해 불필요한 emission을 줄이는 것이 좋습니다.
- **Snapshot Isolation**: snapshotFlow는 Compose의 snapshot 시스템을 따르므로 emission이 isolated snapshot 단위로 흐릅니다. 다른 Flow나 suspending 함수와 결합할 때 snapshot 수명 주기 안에서 동작이 어떻게 보일지 신중하게 검토해야 합니다.

### 요약 {#summary}

<tldr>
snapshotFlow는 Compose의 상태 관찰 시스템과 코틀린 Flow를 잇는 부수 효과 핸들러 API입니다. 분석 이벤트 발송, 데이터 동기화, UI 외 부수 효과처럼 코루틴 연산자가 필요한 시나리오에 잘 어울립니다. snapshotFlow를 잘 이해해 두면 단순한 상태 관찰을 넘어 더 복잡한 Compose 패턴까지 다룰 수 있는 도구가 늘어납니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) ViewModel의 Flow를 직접 관찰하지 않고 snapshotFlow를 선택하는 시나리오는 어떤 경우이며, emission 동작을 어떻게 최적화하시겠습니까?">

가장 자연스러운 시나리오는 **데이터 소스가 ViewModel이 아니라 Compose의 UI 상태일 때** 입니다. `LazyListState` 의 첫 번째 보이는 항목 인덱스, `ScrollState` 의 현재 위치, 텍스트 입력의 길이처럼 Compose가 자체적으로 관리하는 State를 Flow로 다루고 싶다면 ViewModel로 끌어내릴 명분이 약합니다. snapshotFlow는 이런 UI 상태를 그대로 Flow 로 노출시켜, 페이지네이션 트리거나 분석 이벤트 같은 부수 효과를 코루틴 연산자 위에서 깔끔하게 표현할 수 있게 해 줍니다.

emission 동작 최적화는 보통 두 단계로 이뤄집니다. 첫째는 람다 안에서 **정말 필요한 최소한의 상태만 읽는 것** 입니다. snapshotFlow는 람다가 의존하는 모든 snapshot state의 변화를 감지하므로, 람다가 무거운 객체에서 여러 프로퍼티를 읽으면 그만큼 emission이 잦아집니다. 본문 예시처럼 `derivedStateOf` 와 결합해 "정말 의미 있는 boolean 한 줄" 만 흘리도록 좁혀 두는 패턴이 가장 안전합니다. 둘째는 Flow 단계에서 `distinctUntilChanged`, `filter`, `debounce`, `conflate` 같은 연산자로 **emission 흐름을 다듬는 것** 입니다. 같은 이벤트가 의미 없이 여러 번 흘러가면 백엔드 호출이나 분석 이벤트가 중복 발사될 수 있어 이 방어선이 중요합니다.

마지막으로 수집 측에서는 항상 `LaunchedEffect` 같은 컴포지션 인지 코루틴 스코프 안에서 수집하고, 화면이 백그라운드에 있을 때 유지할 필요가 없는 작업이라면 `repeatOnLifecycle(STARTED)` 와 결합해 lifecycle-aware 한 흐름으로 다시 한 번 감싸는 것이 좋습니다. 이렇게 "최소 의존성 → Flow 다듬기 → lifecycle-aware 수집" 의 세 단계를 거치면 snapshotFlow의 강력함을 누리면서도 emission 폭주로 인한 비용을 통제할 수 있습니다.

</def>
</deflist>

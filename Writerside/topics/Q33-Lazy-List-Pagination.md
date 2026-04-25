# Q33) Lazy 리스트 페이지네이션

## Lazy 리스트로 페이지네이션을 어떻게 구현하나요? {#how-to-implement-pagination}

페이지네이션은 큰 데이터셋을 매끄럽게 다루면서도 UI 성능을 유지하기 위한 핵심 패턴입니다. [Jetpack Paging 라이브러리](https://developer.android.com/topic/libraries/architecture/paging/v3-overview)처럼 페이징 데이터를 관리해 주는 표준 솔루션도 있지만, 사용자가 리스트 끝에 다다랐을 때 추가 데이터를 동적으로 불러오는 방식으로 서드파티 라이브러리 없이 무한 스크롤을 구현하는 것도 충분히 가능합니다.

### 스크롤 위치를 감지해 페이지네이션 트리거하기 {#detecting-scroll-position}

가장 흔한 전략은 사용자가 마지막으로 보이는 항목에 가까워졌을 때 데이터 로딩을 트리거하는 것입니다. `LazyListState` 를 활용해 다음과 같이 구현할 수 있습니다.

```kotlin
@Composable
fun PaginatedList(viewModel: ListViewModel) {
    val listState = rememberLazyListState()
    val items by viewModel.items.collectAsStateWithLifecycle()
    val isLoading by viewModel.isLoading.collectAsStateWithLifecycle()
    val threshold = 2
    val shouldLoadMore by remember {
        derivedStateOf {
            val totalItemsCount = listState.layoutInfo.totalItemsCount
            val lastVisibleItemIndex =
                listState.layoutInfo.visibleItemsInfo.lastOrNull()?.index ?: 0
            (lastVisibleItemIndex + threshold >= totalItemsCount) && !isLoading
        }
    }

    LaunchedEffect(listState) {
        snapshotFlow { shouldLoadMore }
            .distinctUntilChanged()
            .filter { it }
            .collect { viewModel.loadMoreItems() }
    }

    LazyColumn(
        state = listState,
        modifier = Modifier.fillMaxSize()
    ) {
        items(items) { item ->
            Text(modifier = Modifier.padding(8.dp), text = "$item")
        }

        item {
            if (isLoading) {
                CircularProgressIndicator(modifier = Modifier.padding(16.dp))
            }
        }
    }
}
```
{title="PaginationExample.kt"}

이 구현에서:

- `LazyListState` 가 스크롤 위치를 관찰합니다.
- `snapshotFlow` 가 마지막으로 보이는 항목 인덱스를 추적합니다.
- 임계치만큼 끝에 다다르면 `loadMoreItems()` 가 호출되어 다음 페이지를 가져옵니다.

### 페이지네이션을 관리하는 ViewModel {#viewmodel-for-pagination}

페이지네이션 로직은 ViewModel 에서 점진적으로 데이터를 불러오도록 다루는 것이 자연스럽습니다.

```kotlin
class ListViewModel : ViewModel() {
    private val _items = mutableStateListOf&lt;Int&gt;()
    val items: StateFlow&lt;List&lt;Int&gt;&gt; = MutableStateFlow(_items).asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow&lt;Boolean&gt; = _isLoading.asStateFlow()

    private var currentPage = 0

    fun loadMoreItems() {
        if (_isLoading.value) return

        _isLoading.value = true
        viewModelScope.launch {
            delay(1000) // 네트워크 요청을 흉내냅니다.
            val newItems = List(20) { (currentPage * 20) + it }
            _items += newItems
            currentPage++
            _isLoading.value = false
        }
    }
}
```
{title="ListViewModel.kt"}

이 구현에서:

- `_items` 는 페이지가 추가될 때마다 갱신되는 StateList 데이터입니다.
- `loadMoreItems()` 는 호출될 때 다음 페이지를 불러옵니다.
- `_isLoading` 은 이미 로딩 중일 때 중복 요청이 일어나지 않도록 막아 줍니다.

### 요약 {#summary}

<tldr>

`LazyListState` 로 더 이상 데이터를 불러와야 할 시점을 감지하면 lazy 리스트에서도 페이지네이션을 자연스럽게 구현할 수 있습니다. 정말 필요한 시점에만 데이터를 가져오므로 불필요한 리컴포지션이 줄고, 큰 데이터셋도 매끄러운 스크롤과 자원 효율을 유지하면서 다룰 수 있습니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 더 많은 항목을 로딩해야 하는 시점을 감지하기 위해 어떤 API와 상태 메커니즘을 활용하시겠습니까?">

기본 도구는 **`LazyListState`**, **`derivedStateOf`**, **`snapshotFlow`** 의 세 축입니다. `LazyListState` 의 `layoutInfo` 는 현재 보이는 항목 인덱스, 전체 항목 수, 첫/마지막 가시 항목 같은 메타데이터를 제공하므로, "마지막 항목 인덱스 + 임계치" 가 전체 개수를 넘어서는지를 직접 계산할 수 있습니다. 이 계산은 스크롤이 일어날 때마다 자주 갱신되는 값을 다루기 때문에, `derivedStateOf` 로 감싸 의미 있는 boolean 한 줄(`shouldLoadMore`) 만 외부로 노출하는 패턴이 가장 정석에 가깝습니다.

이 boolean 을 그대로 컴포저블이 관찰하면 매 스크롤 프레임마다 리컴포지션 후보가 됩니다. 그래서 한 단계 더 감싸서 `LaunchedEffect(listState) { snapshotFlow { shouldLoadMore }.distinctUntilChanged().filter { it }.collect { ... } }` 형태로 다루는 것이 좋습니다. snapshotFlow 가 boolean 의 변화를 Flow 로 노출시켜 주고, `distinctUntilChanged` + `filter { it }` 가 "false → true" 로 바뀌는 그 순간에만 collect 블록을 한 번 트리거합니다. 결과적으로 사용자가 끝에 다다르는 의미 있는 순간에만 한 번 페이지 로딩 콜백이 발생합니다.

여기에 ViewModel 측의 `isLoading` 플래그를 함께 끼워 두면 그림이 완성됩니다. `derivedStateOf` 의 람다 안에서 `&& !isLoading` 을 넣어 두면, 이미 페이지 요청이 진행 중일 때는 boolean 이 false 로 떨어져 추가 요청이 만들어지지 않습니다. 또한 `viewModel.loadMoreItems()` 안에서도 동일한 가드를 두면 사용자가 빠르게 스크롤하더라도 같은 페이지에 대한 중복 요청이 차단됩니다. 이렇게 "측정(LazyListState) → 의미 있는 boolean(derivedStateOf) → 트리거(snapshotFlow) → 가드(isLoading)" 의 네 단계를 묶어 두면 견고한 페이지네이션 트리거 흐름이 됩니다.

</def>
<def title="Q) 페이지네이션에서 LazyListState 의 역할은 무엇이며, derivedStateOf와 snapshotFlow 는 어떤 식으로 데이터 로딩을 최적화해 주나요? distinctUntilChanged() 가 왜 중요한가요?">

`LazyListState` 는 lazy 리스트의 **스크롤 위치와 가시 항목 정보를 실시간으로 노출하는 단일 진실의 원천** 입니다. `firstVisibleItemIndex`, `firstVisibleItemScrollOffset`, `layoutInfo.totalItemsCount`, `layoutInfo.visibleItemsInfo` 같은 프로퍼티가 모두 여기에 모여 있어, 스크롤 기반 페이지네이션의 시그널을 만들기에 가장 자연스러운 출발점이 됩니다. 이 값들은 모두 snapshot state 이므로, 일반 변수처럼 사용하면 자동으로 컴포지션의 의존성에 등록됩니다. 즉 별도의 콜백 없이도 스크롤이 변할 때마다 정확히 영향을 받는 영역만 다시 평가됩니다.

`derivedStateOf` 는 그 위에서 **"의미 있는 변화" 만 골라내는 필터 역할** 을 합니다. 위에서 본 `shouldLoadMore` 처럼 boolean 으로 좁혀 두면, 자주 바뀌는 인덱스/오프셋 값과 무관하게 boolean 이 같은 동안에는 의존하는 컴포저블이 리컴포즈되지 않습니다. 즉 페이지네이션 트리거 같은 자리에서 derivedStateOf 는 "스크롤은 매 프레임 바뀌지만, 이 boolean 은 사용자가 끝에 닿는 순간에만 false → true 로 바뀐다" 라는 매우 좁은 신호로 데이터를 압축해 줍니다.

`snapshotFlow` 는 그 신호를 코루틴 영역으로 끌어올리고, `distinctUntilChanged()` 는 마지막 한 칸의 안전장치를 더해 줍니다. snapshotFlow 자체는 람다가 의존하는 snapshot state 가 변할 때마다 emission 을 만들 수 있는데, 같은 boolean 값이 짧은 시간 안에 여러 번 다시 emit 될 가능성이 남아 있습니다. `distinctUntilChanged()` 가 같은 값의 연속 emission 을 걸러 주므로, 결국 collect 블록이 호출되는 횟수는 boolean 이 실제로 false → true → false 로 토글된 횟수와 일치합니다. 이 한 단계가 빠지면 같은 페이지를 두세 번 요청하는 일이 생기기 쉽고, 그래서 페이지네이션 코드에서 `distinctUntilChanged()` 는 거의 필수에 가깝습니다.

</def>
<def title="Q) 사용자가 빠르게 스크롤할 때 페이지네이션에서 중복된 네트워크 호출이나 데이터 로딩이 일어나지 않게 하려면 어떻게 해야 하나요?">

방어선은 일반적으로 **세 겹** 으로 두는 것이 안전합니다. 첫 번째 방어선은 위에서 설명한 흐름의 끝부분, 즉 **`distinctUntilChanged()` + `filter { it }`** 입니다. 같은 boolean 값이 다시 emit 되더라도 이 두 연산자가 함께 작동해서 collect 블록이 한 번만 트리거되도록 보장합니다.

두 번째 방어선은 ViewModel 의 **`isLoading` 가드** 입니다. 화면 측 컴포저블의 `derivedStateOf` 안에서 `&& !isLoading` 으로 boolean 자체가 false 로 떨어지도록 만들고, `loadMoreItems()` 함수 안에서도 첫 줄에 `if (_isLoading.value) return` 을 두어 직접 호출되어도 중복이 막히도록 합니다. 두 방어선이 함께 있어야 사용자가 빠르게 위아래로 스크롤하면서 boolean 이 빠르게 토글되는 시나리오에서도 안전합니다.

세 번째 방어선은 **요청 단위에서의 멱등성** 입니다. 같은 페이지 번호에 대한 응답이 두 번 도착하더라도 결과가 한 번만 반영되도록, 응답이 도착했을 때 그 페이지가 이미 적용된 상태인지를 검사한 뒤 추가합니다. 또는 페이지 번호 대신 cursor 기반 API 를 사용하고, 마지막으로 받은 cursor 와 응답의 cursor 가 일치할 때만 데이터를 이어 붙이는 식으로 모델링할 수도 있습니다. 마지막으로 매우 빠른 스크롤이 흔한 화면이라면 collect 블록 안에서 `debounce()` 를 한 단계 추가해도 좋습니다. 이렇게 "Flow 단계 → ViewModel 가드 → 응답 멱등성" 의 세 겹을 두면 빠른 스크롤 환경에서도 중복 호출이 사실상 사라집니다.

</def>
</deflist>

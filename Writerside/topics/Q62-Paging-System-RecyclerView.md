# Q62) 페이징 시스템과 RecyclerView

## 큰 데이터셋 로딩에 페이징 시스템이 왜 중요한가요? {#why-paging-matters}

페이징 시스템은 데이터가 많아질수록 그 가치가 빛납니다. 데이터를 작게 쪼갠 페이지(page) 단위로 가져와 화면에 표시함으로써, 앱의 성능과 사용자 경험을 동시에 안정적으로 유지할 수 있기 때문입니다.

데이터를 작은 페이지로 나누어 불러오면 메모리 사용량이 크게 줄어들어, 메모리 부족(out-of-memory) 오류 가능성을 낮출 수 있습니다. 또한 현재 화면에 필요한 데이터만 가져와 렌더링하므로 초기 로딩 속도가 빨라집니다. 추가 데이터를 정말 필요한 시점에만 요청하기 때문에 네트워크 사용량도 최소화되며, 특히 대역폭이 제한된 환경에서 자원 효율이 크게 향상됩니다.

사용자 경험 측면에서도 페이징은 큰 차이를 만듭니다. 사용자가 리스트나 그리드를 스크롤하는 동안 데이터가 동적으로 채워져 자연스러운 스크롤 흐름을 유지할 수 있습니다. 무한 스크롤이나 큰 데이터 소스를 다루는 애플리케이션에 특히 적합한 접근이며, 디바이스나 네트워크에 부담을 주지 않으면서 매끄럽고 반응성 높은 화면을 만들어 줍니다.

### 페이징 시스템 직접 구현하기 {#implementing-manual-paging}

수동으로 페이징 시스템을 구성하려면 다음 단계를 거치면 됩니다.

#### 1. RecyclerView.Adapter와 ViewHolder 만들기 {#step-1-adapter-viewholder}

가장 먼저 `RecyclerView.Adapter` 또는 `ListAdapter`와 그에 대응하는 `ViewHolder`를 정의해야 합니다. 두 컴포넌트는 데이터셋을 RecyclerView에 묶어 주는 핵심 구성 요소입니다. Adapter가 데이터 소스를 관리하고, ViewHolder가 개별 항목의 표시 방식을 정의합니다.

```kotlin
class PokedexAdapter : ListAdapter<Pokemon, PokedexAdapter.PokedexViewHolder>(diffUtil) {

    override fun onCreateViewHolder(
        parent: ViewGroup,
        viewType: Int
    ): PokedexViewHolder {
        val binding = ItemPokemonBinding.inflate(LayoutInflater.from(parent.context))
        return PokedexViewHolder(binding)
    }

    override fun onBindViewHolder(holder: PokedexViewHolder, position: Int) {
        // 항목 바인딩
    }

    inner class PokedexViewHolder(
        private val binding: ItemPokemonBinding,
    ) : RecyclerView.ViewHolder(binding.root) {
        // 바인딩 로직
    }

    companion object {
        private val diffUtil = object : DiffUtil.ItemCallback<Pokemon>() {
            override fun areItemsTheSame(oldItem: Pokemon, newItem: Pokemon): Boolean =
                oldItem.name == newItem.name

            override fun areContentsTheSame(oldItem: Pokemon, newItem: Pokemon): Boolean =
                oldItem == newItem
        }
    }
}
```
{title="ListAdapterExample.kt"}

#### 2. RecyclerView에 addOnScrollListener 추가하기 {#step-2-scroll-listener}

다음으로 RecyclerView의 스크롤 상태를 모니터링하기 위해 `addOnScrollListener`를 등록합니다. 이를 통해 사용자가 마지막으로 보이는 항목까지 스크롤했는지를 감지할 수 있습니다. 마지막 가시 항목이 데이터셋의 끝에 가까워지면 다음 페이지를 네트워크나 데이터베이스에서 가져옵니다. 스크롤이 끊기는 인상을 주지 않으려면 임계값(threshold)을 두어 사용자가 끝에 닿기 전에 미리 데이터를 가져오는 것이 좋습니다.

```kotlin
recyclerView.addOnScrollListener(object : RecyclerView.OnScrollListener() {
    override fun onScrolled(recyclerView: RecyclerView, dx: Int, dy: Int) {
        super.onScrolled(recyclerView, dx, dy)
        val layoutManager = recyclerView.layoutManager as LinearLayoutManager
        val lastVisiblePosition = layoutManager.findLastVisibleItemPosition()

        val thresholds = 4
        if (lastVisiblePosition + thresholds > adapter.itemCount && !viewModel.isLoading) {
            viewModel.loadNextPage()
        }
    }
})
```
{title="AddOnScrollListenerExample.kt"}

#### 3. 새로 받은 데이터셋을 Adapter에 추가하기 {#step-3-update-adapter}

`viewModel.loadNextPage()`가 성공적으로 트리거되면, 새로 받아 온 데이터셋을 `RecyclerView.Adapter`의 기존 데이터 뒤에 이어 붙입니다. 이렇게 함으로써 새 항목이 자연스럽게 리스트에 추가되며, 사용자에게는 끊김 없이 이어지는 스크롤 경험으로 보이게 됩니다.

### 요약 {#summary}

<tldr>

데이터를 페이지 단위로 나누고, RecyclerView의 스크롤 이벤트를 관찰하면서 Adapter를 점진적으로 갱신하면 수동 페이징 시스템을 만들 수 있습니다. 구현 방식은 다양하며, [Jetpack Paging 라이브러리](https://developer.android.com/topic/libraries/architecture/paging/v3-overview)를 활용하면 같은 문제를 더 표준적인 방식으로 해결할 수 있습니다. 학습 자료로는 오픈 소스 라이브러리에서 제공하는 [RecyclerViewPaginator](https://github.com/skydoves/BaseRecyclerViewAdapter?tab=readme-ov-file#recyclerviewpaginator) 같은 커스텀 접근을 살펴보는 것도 도움이 됩니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 앱이 API에서 큰 데이터셋을 받아 RecyclerView에 표시해야 한다면, 부드러운 스크롤과 메모리 사용량 절감을 위해 페이징 시스템을 어떻게 구성하시겠습니까?">

가장 먼저 데이터를 한 번에 다 가져오지 않고 페이지 단위로 받아 오는 흐름을 만들어야 합니다. 서버가 페이지 기반 API를 지원한다면 `page`와 `size` 파라미터를 사용해 일정량씩 요청하고, 그렇지 않다면 마지막 항목의 ID/timestamp를 기반으로 한 cursor 방식으로 다음 페이지를 정의하는 것이 일반적입니다. 클라이언트에서는 ViewModel이 현재 페이지 번호와 로딩 상태를 보유하고, RecyclerView 어댑터에는 이미 받은 데이터만 누적해 넣습니다.

스크롤 동작에 대한 트리거는 `RecyclerView.OnScrollListener`를 활용해 마지막으로 보이는 항목 위치를 감시하는 식으로 구성합니다. 사용자에게 이질감을 주지 않으려면 임계치(threshold)를 두어 끝에 다다르기 전에 미리 다음 페이지를 가져와야 합니다. 또한 동시에 같은 페이지가 두 번 요청되지 않도록 ViewModel에 `isLoading` 같은 플래그를 두고, 응답이 완료된 뒤에만 다음 요청이 가능하도록 만드는 것이 안정적입니다.

화면 상태와 데이터 갱신은 `ListAdapter`와 DiffUtil을 함께 사용하면 부드러워집니다. 새 페이지가 도착했을 때 전체 리스트를 새로 만드는 대신, 기존 리스트에 새 항목을 합친 새 리스트를 `submitList`로 전달하면 DiffUtil이 변화한 부분만 계산해 렌더링합니다. 메모리 압박이 큰 경우에는 화면을 벗어난 항목을 점진적으로 비우거나, 처음부터 [Jetpack Paging](https://developer.android.com/topic/libraries/architecture/paging/v3-overview)을 사용해 윈도우잉(windowing)을 라이브러리에 맡기는 것이 더 합리적입니다.

</def>
<def title="Q) 수동 페이징을 RecyclerView로 구현할 때 마주칠 수 있는 어려움은 무엇이며, 매끄러운 사용자 경험을 위해 어떻게 완화할 수 있을까요?">

수동 페이징의 가장 흔한 함정은 동시 요청 중복입니다. 사용자가 빠르게 스크롤할 때 같은 페이지가 두세 번 요청될 수 있는데, 이 경우 데이터가 중복되어 리스트에 같은 항목이 반복적으로 노출되는 문제가 생깁니다. ViewModel 레벨에서 현재 진행 중인 요청을 추적하고, 응답이 도착하기 전에는 다음 요청을 차단하는 방식으로 막는 것이 기본 방어선입니다.

또 다른 문제는 화면 회전이나 프로세스 재생성으로 인해 누적된 페이지 데이터가 사라지는 상황입니다. ViewModel을 사용해 데이터 캐시를 유지하고, 필요하다면 `SavedStateHandle`이나 Room 기반 로컬 캐시로 더 영속성 있는 보관소를 구성하면 됩니다. Pull-to-refresh 같은 사용자 주도 새로고침을 지원할 때는, 새 데이터로 리스트를 교체하면서 기존 페이지 인덱스도 함께 초기화하는 작업이 빠지면 안 됩니다.

마지막으로 에러 처리와 로딩 상태를 시각적으로 분리해 주는 것이 사용자 경험을 좌우합니다. 첫 페이지 실패는 전체 화면 상태로, 추가 페이지 실패는 리스트 끝의 footer 상태로 분리해 보여 주고, 사용자가 직접 재시도할 수 있는 버튼을 footer에 두는 패턴이 자연스럽습니다. 이러한 구분이 어렵다면 처음부터 Jetpack Paging의 `LoadStateAdapter`처럼 표준화된 추상화를 활용하는 편이 결국 더 깔끔하게 끝납니다.

</def>
</deflist>

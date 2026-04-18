# Q57) Jetpack Paging Library

## Jetpack Paging Library는 무엇인가요? {#what-is-jetpack-paging}

Jetpack Paging 라이브러리는 큰 데이터셋을 페이지(page) 단위로 나눠 점진적으로 불러와 표시하는 작업을 단순화하기 위해 설계된 Android Architecture Components입니다. 데이터베이스나 네트워크 API처럼 대용량 데이터 소스로부터 RecyclerView 기반 UI에 데이터를 효율적으로 공급해야 하는 앱에서 특히 유용합니다.

Paging 라이브러리는 데이터 캐싱, 재시도(retry), 메모리 효율성 같은 핵심적인 부분을 기본 동작으로 제공합니다. Room 데이터베이스 같은 로컬 소스와 네트워크 API 같은 원격 소스를 단독으로 사용할 수도 있고, 두 소스를 조합한 형태(로컬 캐시 + 원격 동기화)로도 사용할 수 있습니다.

### Paging 라이브러리의 주요 구성 요소 {#components}

Paging 라이브러리는 다음과 같은 핵심 구성 요소들이 협력하여 점진적 데이터 로딩을 처리합니다.

1. **PagingData**: 점진적으로 로드되는 데이터의 스트림을 나타냅니다. 관찰(observe)이 가능하며 RecyclerView 같은 UI 컴포넌트에 그대로 전달됩니다.
2. **PagingSource**: 데이터 소스로부터 실제로 페이지를 불러오는 방법을 정의합니다. 위치(position), ID 같은 키를 기반으로 한 페이지 단위 로딩 메서드를 제공합니다.
3. **Pager**: PagingSource와 PagingData 사이를 중개하는 객체로, PagingData 스트림의 수명 주기를 관리합니다.
4. **RemoteMediator**: 로컬 캐시와 원격 API를 조합할 때 경계 조건(예: 더 이상 로컬에 없을 때 네트워크에서 가져오기)을 처리하기 위해 사용합니다.

### Paging 라이브러리의 동작 방식 {#how-it-works}

Paging 라이브러리는 데이터를 페이지 단위로 나눔으로써 효율적인 로딩을 가능하게 합니다. 사용자가 RecyclerView를 스크롤하면 라이브러리가 필요한 시점에 다음 페이지를 가져와 추가하므로, 메모리 사용량을 최소화하면서 자연스러운 스크롤 경험을 만들 수 있습니다. Flow나 LiveData와 결합하여 데이터 변경을 관찰하고 UI에 반영하는 방식이 표준적인 사용 패턴입니다.

일반적인 흐름은 다음과 같습니다.

1. `PagingSource`를 정의하여 데이터를 어떻게 가져올지 명시합니다.
2. `Pager`를 사용해 `PagingData`의 Flow를 만듭니다.
3. ViewModel에서 `PagingData`를 관찰하고, RecyclerView의 `PagingDataAdapter`에 제출하여 화면에 표시합니다.

### Jetpack Paging 사용 예시 {#usage-example}

먼저 네트워크에서 데이터를 가져오는 `PagingSource`를 구현합니다.

```kotlin
class ExamplePagingSource(
    private val apiService: ApiService
) : PagingSource<Int, ExampleData>() {

    override suspend fun load(params: LoadParams<Int>): LoadResult<Int, ExampleData> {
        val page = params.key ?: 1
        return try {
            val response = apiService.getData(page, params.loadSize)
            LoadResult.Page(
                data = response.items,
                prevKey = if (page == 1) null else page - 1,
                nextKey = if (response.items.isEmpty()) null else page + 1
            )
        } catch (e: Exception) {
            LoadResult.Error(e)
        }
    }
}
```
{title="ExamplePagingSource.kt"}

다음으로 Repository 안에서 PagingSource와 PagingData를 중개하는 `Pager`를 만듭니다.

```kotlin
class ExampleRepository(private val apiService: ApiService) {
    fun getExampleData(): Flow<PagingData<ExampleData>> {
        return Pager(
            config = PagingConfig(pageSize = 20),
            pagingSourceFactory = { ExamplePagingSource(apiService) }
        ).flow
    }
}
```
{title="ExampleRepository.kt"}

ViewModel에서는 `PagingData`를 관찰하고, 구성 변경 시에도 데이터 스트림이 살아남도록 `cachedIn(viewModelScope)`을 적용합니다.

```kotlin
class ExampleViewModel(private val repository: ExampleRepository) : ViewModel() {
    val exampleData: Flow<PagingData<ExampleData>> = repository.getExampleData()
        .cachedIn(viewModelScope)
}
```
{title="ExampleViewModel.kt"}

마지막으로 `PagingDataAdapter`를 상속한 RecyclerView Adapter를 만들어 데이터를 화면에 그립니다.

```kotlin
class ExampleAdapter : PagingDataAdapter<ExampleData, ExampleViewHolder>(DIFF_CALLBACK) {

    override fun onBindViewHolder(holder: ExampleViewHolder, position: Int) {
        val item = getItem(position)
        holder.bind(item)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ExampleViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.example_item, parent, false)
        return ExampleViewHolder(view)
    }

    companion object {
        private val DIFF_CALLBACK = object : DiffUtil.ItemCallback<ExampleData>() {
            override fun areItemsTheSame(oldItem: ExampleData, newItem: ExampleData): Boolean {
                return oldItem.id == newItem.id
            }

            override fun areContentsTheSame(oldItem: ExampleData, newItem: ExampleData): Boolean {
                return oldItem == newItem
            }
        }
    }
}
```
{title="ExampleAdapter.kt"}

### 요약 {#summary}

<tldr>

Jetpack Paging 라이브러리는 점진적인 데이터 로딩 구현을 도와주는 도구입니다. PagingSource, Pager, PagingDataAdapter 같은 핵심 구성 요소가 협력해 큰 데이터셋의 처리 부담을 라이브러리 쪽으로 옮겨 줍니다. 무한 스크롤, 페이지네이션 API, 대규모 데이터베이스를 다루는 앱에서 특히 유용하며, 개발자는 데이터 fetching이나 UI 갱신 같은 반복적인 작업 대신 애플리케이션 로직 자체에 집중할 수 있습니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Paging 라이브러리는 데이터 로딩 중 발생하는 에러를 어떻게 처리하며, 페이지네이션 흐름에서 권장되는 에러 처리와 재시도 전략은 무엇인가요?">

Paging 라이브러리는 `PagingSource.load()` 안에서 발생한 예외를 `LoadResult.Error(throwable)`로 감싸 반환하는 방식으로 에러를 표현합니다. 이 결과는 그대로 PagingData 스트림에 흘러가서 `PagingDataAdapter.loadStateFlow`(또는 `addLoadStateListener`)를 통해 UI 레이어에서 관찰할 수 있습니다. 즉 페이지 로딩 중 일어난 네트워크 실패는 어댑터의 LoadState로 표면화되며, 어떤 페이지(refresh, prepend, append) 로딩에서 실패가 일어났는지까지 구분해서 받아 볼 수 있습니다.

권장되는 처리 패턴은 두 갈래입니다. 첫째, 사용자가 직접 재시도할 수 있는 UI를 제공하고 그 버튼이 `PagingDataAdapter.retry()`를 호출하도록 만드는 것입니다. retry는 마지막에 실패한 페이지 로딩만 다시 트리거하므로, 이미 성공적으로 불러온 페이지를 다시 가져오는 낭비가 없습니다. 둘째, 실패 종류별로 UX를 다르게 보여주는 것이 좋습니다. 일반적으로 첫 페이지 실패(refresh error)는 전체 화면 단위의 에러 상태로, append/prepend 실패는 리스트 끝에 인라인으로 보여 주는 footer/header 형태로 처리합니다. `PagingDataAdapter`에는 이를 위한 `withLoadStateFooter`, `withLoadStateHeader`, `withLoadStateHeaderAndFooter` 헬퍼가 제공됩니다.

PagingSource 자체에서는 일시적 실패를 자동으로 다시 시도하는 로직을 직접 두지 않는 것이 일반적입니다. 라이브러리가 제공하는 retry 메커니즘과 OkHttp 인터셉터 같은 네트워크 레벨의 재시도/타임아웃 정책을 조합하는 편이, 페이지 키 정합성을 깨뜨리지 않으면서 깔끔하게 동작합니다. 데이터 소스가 무효화되어야 할 정도의 큰 변화(예: 인증 토큰 만료 후 재로그인)에는 `PagingSource.invalidate()`를 호출해 새로운 PagingSource로 처음부터 다시 로딩되도록 하는 것이 적절합니다.

</def>
</deflist>

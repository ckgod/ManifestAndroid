# Q32) 효율적인 리스트 렌더링

## UI jank 없이 수백 개 항목을 어떻게 효율적으로 렌더링하나요? {#how-to-render-many-items}

수백, 수천 개의 항목을 한 화면에 보여 줘야 할 때 일반 `Column` 같은 표준 레이아웃을 그대로 쓰면 불필요한 컴포지션과 렌더링이 누적되어 성능 문제가 생깁니다. UI jank를 피하고 효율을 끌어올리기 위해 Jetpack Compose는 [Lazy List](https://developer.android.com/develop/ui/compose/lists#lazy)라는 최적화된 리스트 컴포넌트를 제공합니다. **LazyColumn**, **LazyRow**, **LazyGrid** 같은 컴포넌트가 항목들을 동적으로 컴포즈하고 재활용해 줍니다.

### LazyColumn으로 세로 리스트 다루기 {#lazycolumn}

`LazyColumn` 은 보이는 항목만 컴포즈하고 화면 밖으로 사라진 항목은 재활용하여 큰 리스트를 효율적으로 그리도록 설계된 컴포저블입니다. 메모리 사용량이 크게 줄고, 스크롤 성능도 안정적으로 유지됩니다.

```kotlin
@Composable
fun ItemList() {
    LazyColumn {
        items(1000) { index ->
            Text(text = "Item #$index", modifier = Modifier.padding(8.dp))
        }
    }
}
```
{title="LazyColumnExample.kt"}

이 예시에서:

- `LazyColumn` 은 보이는 항목만 로드하므로 불필요한 컴포지션이 발생하지 않습니다.
- `items` 함수가 1,000개를 미리 다 만들지 않고 필요할 때만 동적으로 생성합니다.

### LazyRow로 가로 리스트 다루기 {#lazyrow}

가로 방향 스크롤 리스트에는 `LazyRow` 가 같은 원리로 동작합니다.

```kotlin
@Composable
fun HorizontalItemList() {
    LazyRow {
        items(500) { index ->
            Text(text = "Item #$index", modifier = Modifier.padding(8.dp))
        }
    }
}
```
{title="LazyRowExample.kt"}

가로 항목이 많아질 때 UI lag 을 막아 줍니다.

### LazyVerticalGrid로 그리드 레이아웃 다루기 {#lazyverticalgrid}

그리드 구조가 필요한 경우 `LazyVerticalGrid` 가 `LazyColumn` 과 동일한 효율을 유지하면서 항목들을 열 단위로 배치해 줍니다.

```kotlin
@Composable
fun GridItemList() {
    LazyVerticalGrid(
        columns = GridCells.Fixed(3),
        modifier = Modifier.fillMaxSize()
    ) {
        items(300) { index ->
            Text(text = "Item #$index", modifier = Modifier.padding(8.dp))
        }
    }
}
```
{title="LazyGridExample.kt"}

특정 시점에 보이는 그리드 항목만 컴포즈되도록 보장됩니다. 가로 방향 그리드가 필요하다면 `LazyHorizontalGrid` 를 같은 패턴으로 사용할 수 있습니다.

### 키(Key)로 성능 최적화하기 {#optimizing-with-keys}

기본 동작에서는 각 항목의 상태가 리스트/그리드 안의 위치(position)와 묶여 있습니다. 그런데 데이터셋이 바뀌어 항목이 추가·삭제·재정렬되면 위치가 흔들리고, 그 결과 항목 상태가 잘못된 자리에 매칭되어 사라지거나 어긋나기 쉽습니다. 자주 재활용되는 리스트에서 항목 상태를 보존하려면 **각 항목에 고유한 키를 지정** 해야 합니다. 그러면 항목 위치가 바뀌더라도 상태가 그 항목에 그대로 따라가고, 불필요한 리컴포지션도 줄어듭니다.

```kotlin
@Composable
fun KeyedItemList(items: List<Item>) {
    LazyColumn {
        items(items, key = { it.id }) { item ->
            Text(text = item.name, modifier = Modifier.padding(8.dp))
        }
    }
}
```
{title="LazyColumnWithKeys.kt"}

`key = { it.id }` 가 각 항목에 고유 식별자를 부여해, 리스트가 바뀔 때 불필요한 리컴포지션을 막아 줍니다. 더 자세한 내용과 베스트 프랙티스는 공식 문서 [Use lazy layout keys](https://developer.android.com/develop/ui/compose/performance/bestpractices#use-lazylist-keys)에서 확인할 수 있습니다.

> **추가 팁**: `LazyColumn` 이나 `LazyRow` 의 `key` 파라미터는 시그니처상으로는 옵셔널이지만, Google 엔지니어들은 GDE 활동 등에서 이를 **필수**처럼 다루기를 강하게 권장합니다. lazy 리스트의 성능을 충분히 끌어내고 안정적인 상태 보존을 보장하려면 `key` 를 정확하게 지정해야 합니다. 또한 여러 항목이 같은 키를 갖게 되면 앱이 **반드시** 예외를 던지므로, 백엔드가 항목별 고유 ID를 제공하도록 만들어 두는 것이 가장 안전합니다. 중복 ID가 들어올 가능성이 있다면 `items.distinctBy { it.id }` 같은 식으로 lazy 리스트에 전달하기 전에 미리 걸러 내야 크래시를 막을 수 있습니다.

### 요약 {#summary}

<tldr>

큰 리스트를 효율적으로 렌더링하려면 표준 `Column`/`Row` 대신 **LazyColumn**, **LazyRow**, **LazyGrid** 같은 lazy 리스트를 사용해야 합니다. 여기에 **키(key)** 까지 적용해 두면 동적인 데이터 변화에서도 리컴포지션이 최소화되어, UI jank 없이 매끄럽고 효율적인 리스트 렌더링을 만들 수 있습니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 실시간 메시지가 흐르는 채팅 화면을 만든다면, 부드러운 스크롤과 최소한의 리컴포지션 비용을 위해 레이아웃을 어떻게 구성하시겠습니까?">

가장 먼저 정해야 할 부분은 **데이터 모델과 키 전략** 입니다. 메시지마다 안정적이고 고유한 ID(서버에서 발급한 messageId)를 보장하고, `LazyColumn(items, key = { it.id }) { ... }` 형태로 그 ID를 키로 사용해야 합니다. 추가/삭제/재정렬이 잦은 채팅 화면에서는 키가 항목 상태(이미지 로딩 상태, 셀 내부 애니메이션, 셀별 입력)를 안정적으로 따라가게 만들고, 새 메시지가 도착해도 다른 셀이 다시 그려지지 않도록 만들어 줍니다. 메시지 종류가 다양하다면 `contentType = { it::class }` 도 함께 지정해 LazyColumn 의 셀 재사용 효율을 끌어올릴 수 있습니다.

레이아웃 측면에서는 **역방향 스크롤(reverseLayout = true)** 과 **`LazyListState` 의 활용** 이 핵심입니다. 채팅은 보통 최근 메시지가 아래쪽에 보이는 형태이므로 `reverseLayout = true` 와 함께 데이터를 시간 역순으로 정렬해 두면, 새 메시지가 도착했을 때 자동으로 가장 아래에 추가되는 자연스러운 흐름이 만들어집니다. 사용자가 직접 위로 스크롤해 과거 메시지를 보고 있는 경우에는 자동으로 끝까지 끌고 내려가지 않도록, `firstVisibleItemIndex` 가 0인 경우(=가장 최근 항목 근처)에만 `animateScrollToItem(0)` 을 호출하는 식으로 조건부 스크롤을 다뤄야 합니다.

리컴포지션 비용을 더 줄이려면 **셀 컴포저블의 stability** 를 챙기는 것이 결정적입니다. 메시지 데이터 클래스를 `@Immutable` 로 두고, 클릭/롱프레스 핸들러는 ViewModel 메서드 참조나 `remember(message.id)` 로 동일성을 유지하며, 화면 내 입력 상태는 ViewModel 의 StateFlow 로 끌어올려 셀로는 그대로 흘려보냅니다. 마지막으로 자주 호출되는 `derivedStateOf` 로 "스크롤이 끝에 닿았는가" 같은 boolean 한 줄만 관찰하면, 메시지가 매 초 흘러도 화면 전체가 따라 움직이지 않도록 만들 수 있습니다.

</def>
<def title="Q) LazyColumn 이나 LazyGrid 의 key 는 리스트가 갱신될 때 UI 성능과 안정성에 어떻게 도움을 주나요?">

`key` 의 역할을 한 줄로 표현하면 **"위치(position)가 아니라 정체성(identity)으로 항목을 추적하라"** 입니다. lazy 리스트는 기본적으로 항목의 컴포지션 상태와 cache slot 을 위치 기준으로 관리합니다. 그래서 항목이 추가되거나 정렬이 바뀌면 같은 위치에 있던 다른 항목이 들어오게 되고, 이전 항목이 가지고 있던 내부 상태(애니메이션 진행도, 이미지 로딩 결과, 사용자 입력)가 새 항목에 잘못 매칭되거나 통째로 사라지는 일이 생깁니다. `key = { it.id }` 를 지정해 두면 lazy 리스트가 같은 ID를 가진 항목을 동일한 컴포지션 슬롯에 매핑해, 위치가 바뀌어도 상태가 항목과 함께 따라갑니다.

성능 측면에서도 키는 적지 않은 차이를 만듭니다. 키가 없을 때는 리스트가 갱신될 때마다 lazy 리스트가 어떤 위치의 항목이 바뀌었는지 정확히 판단할 수 없어, 안전한 쪽으로 더 많은 컴포저블을 다시 컴포즈합니다. 키가 있으면 lazy 리스트가 "추가/제거/이동" 을 정확히 분리해 인식할 수 있고, 그 결과 정말 변화가 일어난 항목만 갱신할 수 있습니다. 또한 항목 진입/이탈 애니메이션(`Modifier.animateItemPlacement()` 등)도 키 기반으로 동작하므로, 키가 없으면 자연스러운 트랜지션 자체가 깨집니다.

마지막으로 **키는 안정적이고 고유해야** 합니다. 인덱스나 해시처럼 위치/내용에 따라 바뀌는 값을 키로 쓰면 사실상 키가 없는 것과 같은 효과가 납니다. 또 다른 함정은 중복 키입니다. 두 항목이 같은 키를 갖게 되면 lazy 리스트가 즉시 예외를 던지므로, 데이터 소스 단계에서 `distinctBy { it.id }` 같은 가드를 두거나, 백엔드가 정말 고유한 ID를 발급하도록 보장해 두는 것이 안전합니다. 정체성이 분명한 키 — 이 한 가지가 lazy 리스트의 효율과 안정성 모두를 동시에 끌어올려 주는 열쇠입니다.

</def>
</deflist>

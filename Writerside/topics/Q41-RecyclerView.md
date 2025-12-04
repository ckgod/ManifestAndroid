# Q41) RecyclerView

## RecyclerView는 내부적으로 어떻게 작동하나요? {#how-recyclerview-works-internally}

RecyclerView는 새 뷰를 반복적으로 인플레이션하는 대신 항목 뷰를 재활용하여 대규모 데이터셋을 효율적으로 표시하도록 설계된 유용하고 유연한 Android 컴포넌트입니다.
이는 `ViewHolder` 패턴으로 알려진 `Object Pool`과 유사한 메커니즘을 사용하여 뷰를 관리함으로써 이러한 효율성을 달성합니다.

### RecyclerView 내부 메커니즘의 핵심 개념 {#core-concepts}

1.  **뷰 재활용**: `RecyclerView`는 데이터셋의 모든 항목에 대해 새 뷰를 생성하는 대신 기존 뷰를 재사용합니다. 뷰가 가시 영역 밖으로 스크롤될 때, 해당 뷰는 파괴되지 않고 뷰 풀(`RecyclerView.RecycledViewPool`로 알려짐)에 추가됩니다. 새 항목이 시야에 들어올 때, `RecyclerView`는 가능한 경우 이 풀에서 기존 뷰를 검색하여 인플레이션 오버헤드를 방지합니다.
2.  **ViewHolder 패턴**: `RecyclerView`는 `ViewHolder`를 사용하여 항목 레이아웃 내 뷰에 대한 참조를 저장합니다. 이는 바인딩 중 `findViewById()` 호출을 반복적으로 방지하여 레이아웃 순회 및 뷰 조회 횟수를 줄여 성능을 향상시킵니다.
3.  **Adapter의 역할**: `RecyclerView.Adapter`는 데이터 소스와 `RecyclerView`를 연결합니다. `Adapter`의 `onBindViewHolder()` 메서드는 뷰가 재사용될 때 데이터를 뷰에 바인딩하여, 가시적인 항목만 업데이트되도록 합니다.
4.  **RecycledViewPool**: `RecycledViewPool`은 사용되지 않는 뷰가 저장되는 `Object Pool` 역할을 합니다. 이는 `RecyclerView`가 유사한 뷰 유형을 가진 여러 목록 또는 섹션에서 뷰를 재사용할 수 있도록 하여 메모리 사용량을 더욱 최적화합니다.

### 재활용 메커니즘 작동 방식 {#how-recycling-mechanism-works}

1.  **스크롤 및 항목 가시성**: 사용자가 스크롤함에 따라 시야에서 벗어나는 항목은 `RecyclerView`에서 분리되지만 파괴되지는 않습니다. 대신 `RecycledViewPool`에 추가됩니다.
2.  **재활용 뷰에 데이터 다시 바인딩**: 새 항목이 시야에 들어올 때, `RecyclerView`는 먼저 `RecycledViewPool`에서 필요한 유형의 사용 가능한 뷰를 확인합니다. 일치하는 항목을 찾으면 `onBindViewHolder()`를 사용하여 새 데이터로 뷰를 다시 바인딩하여 재사용합니다.
3.  **사용 가능한 뷰가 없는 경우 인플레이션**: 풀에 적합한 뷰가 없으면 `RecyclerView`는 `onCreateViewHolder()`를 사용하여 새 뷰를 인플레이션합니다.
4.  **효율적인 메모리 사용량**: 뷰를 재활용함으로써 `RecyclerView`는 메모리 할당 및 가비지 컬렉션을 최소화하여 대규모 데이터셋 또는 빈번한 스크롤이 포함된 시나리오에서 성능 문제를 일으킬 수 있는 요소를 줄입니다.

다음은 기본적인 `RecyclerView` 구현 예시입니다:

```kotlin
class MyAdapter(private val dataList: List<String>) : RecyclerView.Adapter<MyAdapter.MyViewHolder>() {

    class MyViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        val textView: TextView = itemView.findViewById(R.id.textView)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): MyViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_layout, parent, false)
        return MyViewHolder(view)
    }

    override fun onBindViewHolder(holder: MyViewHolder, position: Int) {
        holder.textView.text = dataList[position]
    }

    override fun getItemCount(): Int = dataList.size
}
```

### RecyclerView의 Object Pool 접근 방식의 장점 {#advantages-object-pool-approach}

1.  **향상된 성능**: 뷰를 재사용하면 새 레이아웃을 인플레이션하는 오버헤드가 줄어들어 스크롤이 더 부드러워지고 성능이 향상됩니다.
2.  **효율적인 메모리 관리**: `Object Pool`은 뷰를 재활용하여 메모리 할당을 최소화하고 빈번한 가비지 컬렉션을 방지합니다.
3.  **맞춤 설정**: `RecycledViewPool`은 각 유형의 최대 뷰 수를 관리하도록 맞춤 설정할 수 있어, 개발자가 특정 사용 사례에 맞게 동작을 최적화할 수 있습니다.

### 요약 {#summary}

`RecyclerView`는 사용되지 않는 뷰가 `RecycledViewPool`에 저장되고 필요할 때 재사용되는 효율적인 `Object Pool` 메커니즘을 사용합니다. 이 디자인은 `ViewHolder` 패턴과 결합되어 메모리 사용량을 최소화하고 레이아웃 인플레이션 오버헤드를 줄이며 성능을 향상시켜 `RecyclerView`를 Android 애플리케이션에서 대규모 데이터셋을 표시하는 데 필수적인 도구로 만듭니다.

<deflist collapsible="true" default-state="collapsed">
<def title="RecyclerView의 ViewHolder 패턴은 ListView와 비교하여 성능을 어떻게 향상시키나요?">

RecyclerView가 ListView에 비해 성능상 우위를 점하는 핵심은 ViewHolder 패턴을 강제하여 `findViewById()` 호출 비용을 획기적으로 줄이기 때문입니다.

**1. `findViewById()` 호출 최소화**

가장 큰 차이점은 뷰 객체 탐색의 빈도입니다. 

* **ListView (기본 구현 시)**: `getView()`가 호출될 때마다 `findViewById()`를 수행하여 아이템 내부의 텍스트뷰나 이미지뷰를 찾습니다. `findViewById()`는 뷰 계층 구조를 순회하며 ID를 찾는 과정으로, 비용이 꽤 높은 연산입니다. 스크롤 할 때마다 이 연산이 반복되면 프레임 드랍이 발생할 수 있습니다.
* **RecyclerView**: ViewHolder 객체 생성 시점에 `findViewById()`를 단 한 번만 수행하고, 찾아낸 뷰의 참조를 ViewHolder 필드에 저장(캐싱)해 둡니다. 이후 스크롤이 발생하여 데이터를 다시 바인딩할 때는 저장된 참조를 그대로 사용하므로 탐색 비용이 0에 수렴합니다.

**2. 생성과 바인딩의 명확한 분리**

RecyclerView는 아키텍처 레벨에서 뷰의 생성(`onCreateViewHolder`)과 데이터 연결(`onBindViewHolder`)을 분리합니다.

* **ListView**: `getView()`메서드 하나에서 뷰의 생성(또는 재사용)과 데이터 바인딩을 모두 처리해야 하므로, 개발자가 실수로 최적화 코드를 누락할 가능성이 높습니다.
* **RecyclerView**: 무거운 작업인 '뷰 생성 및 뷰 홀더 생성'은 필요할 때만 수행하고, 스크롤 시 빈번하게 일어나는 '데이터 바인딩'만 가볍게 처리하도록 강제합니다.

</def>
<def title="RecyclerView에서 ViewHolder의 생성부터 재활용까지의 수명 주기를 설명하세요.">

전체 과정은 크게 **생성(Creation) -> 바인딩(Binding) -> 사용(Active) -> 재활용(Recycling)** 의 단계로 나뉩니다.

**1. 생성 단계**

스크롤 등으로 인해 새로운 아이템을 보여줘야 하는데, 재사용할 수 있는 ViewHolder가 없을 때 발생합니다. 
가장 비용이 많이 드는 단계입니다.

* `onCreateViewHolder()`호출
  * xml 레이아웃을 객체화(inflate)합니다.
  * ViewHolder 객체를 생성하고, 내부적으로 `findViewById()`를 수행하여 뷰 참조를 캐싱합니다.
  * 이 단계는 화면에 보이는 아이템 개수 + 여유분만큼만 실행되며, 이후에는 거의 호출되지 않습니다.

**2. 바인딩 단계**

생성된 ViewHolder(또는 재활용된 ViewHolder)에 실제 데이터를 입히는 과정입니다. 

* `onBindViewHolder()`호출
  * ViewHolder가 가진 뷰(TextView, ImageView 등)에 현재 위치(Position)에 맞는 데이터를 설정합니다. 
  * 스크롤 할 때마다 빈번하게 호출되므로, 이곳에서 복잡한 연산이나 객체 생성을 하면 스크롤 끊김이 발생할 수 있습니다.

**3. 활성 상태**

* `onViewAttachedToWindow()`: 뷰가 윈도우에 연결되어 화면에 보이기 직전에 호출됩니다. 애니메이션 시작 등의 작업에 유용합니다.
* 화면 표시: 사용자가 실제로 보고 조작하는 상태입니다.

**4. 스크롤 및 재활용 단계**

아이템이 화면 밖으로 스크롤 되면 ViewHolder는 즉시 삭제되지 않고 캐시(Cache) 또는 풀(Pool)로 이동합니다.

* 1차: Scrap Heap & Cache (재사용 우선)
  * 화면에서 살짝 벗어난 뷰는 스크랩(Scrap)또는 캐시(Cache)에 저장됩니다.
  * 특징: 데이터가 그대로 유지되어 있습니다. 사용자가 다시 반대 방향으로 스크롤하여 돌아오면, `onBindViewHolder()` 호출 없이 즉시 다시 보여집니다.
* 2차: RecycledViewPool
  * 캐시가 꽉 차면, 가장 오래된 뷰는 RecycledViewPool로 이동합니다.
  * `onViewRecycled()`뷰가 풀로 이동하기 전 호출됩니다. 여기서 리소스 해제를 할 수 있습니다.
  * 뷰의 레이아웃만 남고 데이터는 Dirty 상태로 간주됩니다.
  * 다른 위치의 아이템이 필요할 때 이 풀에서 뷰를 꺼내오며, 이 때는 데이터가 맞지 않으므로 반드시 `onBindViewHolder()`를 다시 실행하여 새 데이터를 입힙니다.

</def>
<def title="RecycledViewPool은 무엇이며, 뷰 항목 렌더링을 최적화하는 데 어떻게 사용될 수 있나요?">

RecycledViewPool은 RecyclerView에서 스크롤로 인해 화면에서 사라진 ViewHolder 객체를 보관하고 관리하는 저장소입니다.

기본적으로 RecyclerView 내부에서 동작하지만, 개발자가 명시적으로 개입하여 여러 RecyclerView 간에 이 풀을 공유할 때 성능 최적화가 극대화 됩니다.

**1. RecycledViewPool의 기능**

* 분류 저장: 뷰를 `itemType`별로 구분하여 저장합니다.
* 데이터 초기화: 이곳에 들어온 ViewHolder는 데이터가 더럽혀진(dirty) 상태로 간주됩니다. 따라서 여기서 꺼내 쓸 때는 반드시 `onBindViewHolder()`가 실행됩니다.
* 생성 억제: `onCreateViewHolder()`(레이아웃 인플레이션) 호출을 막아 메모리 할당과 CPU 연산을 줄입니다.

**2. 최적화 활용 방법: 중첩된 RecyclerView**

수직 리스트 안에 수평 리스트가 있는 구조에서 RecycledViewPool을 사용해 성능을 최적화 할 수 있습니다.

**최적화 전**

* 사용자가 아래로 스크롤하여 새로운 '수평 리스트(Row B)'가 화면에 나타날 때, Row B는 자신만의 뷰 풀을 새로 만듭니다.
* 이미 화면 밖으로 나간 '수평 리스트(Row A)'가 가지고 있던 뷰들은 재사용되지 못하고 메모리에서 낭비되거나 GC 대상이 됩니다.
* 스크롤 할 때마다 수평 아이템들을 새로 생성하느라 버벅거림이 발생합니다.

**최적화 후 (공유 풀 사용)**

모든 수평 RecyclerView가 하나의 RecycledViewPool을 공유하도록 설정합니다.

* 설정: 부모(수직) RecyclerView의 어댑터에서 자식(수평) RecyclerView를 생성할 때, 미리 만들어둔 단일 Pool 객체를 `setRecycledViewPool()`로 주입합니다.
* 동작
  * Row A가 화면 밖으로 나가면, 그 안의 카드 뷰들이 공유 풀로 반환됩니다. 
  * Row B가 화면에 들어올 때, 뷰를 새로 만들지 않고 공유 풀에서 Row A가 쓰던 뷰를 꺼내와 데이터만 바인딩합니다.

</def>
</deflist>
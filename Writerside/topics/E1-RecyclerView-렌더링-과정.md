# E1) RecyclerView 렌더링 과정

## RecyclerView 렌더링 과정 상세 분석
전체 과정은 크게 **1) 데이터 설정 및 변경 알림**, **2) 측정 (`Measure`)**, **3) 레이아웃 (`Layout`)**, **4) 그리기 (`Draw`)** 의 4단계로 나뉩니다. 이 모든 과정은 안드로이드 `UI` 렌더링의 핵심인 `VSYNC` 신호에 맞춰 한 프레임(약 16.67ms) 안에 이루어지려 시도합니다.

## 0단계: 전제 조건 및 초기 설정

- ViewType: (`A`, `B`, `C`, ..., `Z`)
- 각 뷰타입에 해당하는 뷰홀더 뷰의 높이는 wrap_content로 지정되어 있습니다.
- `RecyclerView`는 이미 초기화되어 있습니다.
- `LayoutManager`(예: `LinearLayoutManager`)와 `Adapter`가 설정되어 있다고 가정합니다.


> `setLayoutManager()`: `RecyclerView`에게 아이템을 어떻게 배치할지(예: 세로, 가로, 그리드) 결정하는 규칙 관리자를 지정합니다. 
> 
> `setAdapter()`: `RecyclerView`에게 어떤 데이터를 어떻게 `View`로 만들어 보여줄지 정의하는 어댑터를 지정합니다. 이때 어댑터의 `getItemViewType()` 메서드는 각 포지션에 어떤 종류의 뷰(`A`, `B`, `C`...)가 와야 하는지 식별하는 데 사용됩니다.

## 1단계: 데이터 설정 및 변경 알림

`adapter.submitList(newList)` 또는 `adapter.notifyDataSetChanged()` 호출

1.  데이터 변경 감지: 어댑터에 새로운 리스트(`A`, `B`, `C`, ..., `Z`)가 전달됩니다. `ListAdapter`의 `submitList`를 사용하면 `DiffUtil`이 백그라운드 스레드에서 이전 리스트와 새 리스트의 차이점을 계산하여 효율적인 업데이트(삽입, 삭제, 변경)를 지시합니다. 이 시나리오에서는 처음 리스트를 설정하는 것이므로 "`0`개의 아이템에서 `26`개의 아이템이 삽입되었다"는 `onItemRangeInserted(0, 26)` 이벤트가 발생합니다.
2.  `RecyclerView`에 변경 알림: 어댑터는 내부적으로 `RecyclerViewDataObserver`를 통해 `RecyclerView`에 데이터셋이 변경되었음을 알립니다.
3.  레이아웃 요청 (`requestLayout`): 데이터 변경을 감지한 `RecyclerView`는 자신의 상태가 '더럽다'(`dirty`)고 표시하고, `View` 계층 구조(`View Hierarchy`)에 새로운 레이아웃 패스가 필요함을 알리기 위해 **`requestLayout()`** 을 호출합니다. 이는 "나와 내 자식들의 크기와 위치를 다시 계산해야 해!"라고 시스템에 요청하는 신호입니다. 이 호출은 다음 `VSYNC` 신호에 맞춰질 측정(`Measure`) 및 레이아웃(`Layout`) 과정을 예약합니다.

## 2단계: `RecyclerView`의 측정 (`Measure`) 과정

`requestLayout()` 호출로 인해 `View` 계층의 최상위 뷰부터 측정(`Measure`) 과정이 시작됩니다.

1.  부모 뷰에서 `RecyclerView` 측정: `RecyclerView`를 감싸고 있는 부모 레이아웃(예: `ConstraintLayout`, `FrameLayout`)이 자신의 `onMeasure()` 메서드 내에서 `RecyclerView`의 `measure()`를 호출합니다. 이때 부모는 `RecyclerView`에 대한 제약 조건이 담긴 `MeasureSpec`을 전달합니다.
    -   `widthMeasureSpec`: 보통 `MATCH_PARENT`이므로 `EXACTLY` 모드와 부모의 너비 값이 전달됩니다.
    -   `heightMeasureSpec`: `RecyclerView`의 높이 또한 `MATCH_PARENT`나 고정 `dp` 값이라면 `EXACTLY` 모드가, `WRAP_CONTENT`라면 `AT_MOST` 모드가 전달됩니다.
2.  `RecyclerView.onMeasure()`: `RecyclerView`는 자신의 크기를 스스로 결정하지 않습니다. 이 책임을 `LayoutManager`에게 위임합니다.
3.  `LayoutManager.onMeasure()`가 호출됩니다.
4.  `LayoutManager.onMeasure()`: `LinearLayoutManager`를 예로 들면, 이제 화면에 채울 아이템들을 실제로 생성하고 측정하여 `RecyclerView`가 차지할 전체 높이를 계산해야 합니다.

### 아이템 뷰 생성 및 측정 (`A`, `B`, `C`, `D`, `E`...)

1.  `LayoutManager`는 화면에 표시될 첫 번째 아이템(`A`, `position 0`)부터 채우기 시작합니다.
2.  `LayoutManager`는 `Recycler` 객체에게 "`position 0`에 해당하는 `View`를 줘"라고 요청합니다.

#### **`Recycler`** 의 동작:

1.  먼저, 스크랩 뷰(`Scrap View`)나 캐시(`Cache`)에 재사용할 뷰가 있는지 확인합니다. (초기 로딩이므로 아무것도 없습니다.)
2.  다음으로 **`RecycledViewPool`**에서 재사용할 `ViewHolder`가 있는지 확인합니다. 이때 `getItemViewType(0)`을 호출하여 `View` 타입 '`A`'에 해당하는 `Pool`을 확인합니다. (초기 로딩이므로 역시 비어있습니다.)
3.  재사용할 뷰가 없으므로, `Recycler`는 **`adapter.createViewHolder(parent, viewTypeA)`**를 호출합니다.

#### `adapter.createViewHolder()` - `Inflate` 과정:

1.  이 메서드 내에서 개발자가 구현한 대로 `LayoutInflater.inflate(R.layout.item_a, parent, false)`가 실행됩니다.
2.  `inflate`는 `XML` 레이아웃 파일을 파싱하여 실제 `View` 객체들(예: `TextView`, `ImageView`)을 메모리에 생성하고 트리 구조를 만듭니다. 이 과정은 `I/O` 및 반사(`Reflection`)를 포함하므로 비교적 무거운 작업입니다.
3.  생성된 `View` 객체는 `ViewHolderA`로 감싸져 반환됩니다.

#### `adapter.bindViewHolder(holderA, 0)`:

`ViewHolder`가 생성되면, 해당 `position(0)`의 데이터('`A`' 아이템 데이터)를 `View`에 바인딩(연결)합니다. 예를 들어, `holder.textView.setText(...)` 등이 실행됩니다.

#### 자식 뷰(`ItemView`) 측정:

1.  이제 '`A`' 타입의 아이템 뷰(`itemView`)가 준비되었습니다. `LayoutManager`는 이 뷰의 크기를 알아내기 위해 `measureChildWithMargins(itemView, ...)`와 같은 메서드를 호출합니다.
2.  이로 인해 `itemView`의 `measure()` 메서드가 호출되고, 이는 다시 `itemView.onMeasure()`를 호출합니다.
3.  `itemView`의 높이가 `wrap_content`이므로, `itemView`는 자신이 포함한 모든 자식 뷰(`TextView`, `ImageView` 등)를 먼저 측정하여 그들의 크기를 알아내고, 그 크기들과 패딩(`padding`) 값을 조합하여 자신의 최종 높이를 결정합니다. 예를 들어, `TextView`가 `wrap_content`라면 내부 텍스트의 줄 수와 글자 크기에 따라 높이가 결정됩니다.
4.  측정이 완료되면 `itemView`는 `setMeasuredDimension(width, height)`를 호출하여 자신의 크기를 저장합니다.

반복: `LayoutManager`는 '`A`' 아이템 뷰의 측정된 높이를 얻습니다. 아직 `RecyclerView`의 높이를 채우지 못했으므로, 다음 아이템인 '`B`' (`position 1`)에 대해 위의 (생성 -> 바인딩 -> 측정) 과정을 완벽하게 동일하게 반복합니다.

이 과정은 화면에 `A`, `B`, `C`, `D`, `E`가 모두 보일 때까지, 즉 측정된 아이템들의 높이 합이 `RecyclerView`에 할당된 높이(부모가 전달한 `heightMeasureSpec`)를 채울 때까지 계속됩니다. `LayoutManager`는 화면에 보이는 것보다 약간 더 많은 아이템(`prefetch`)을 미리 준비할 수도 있습니다.

`RecyclerView` 최종 높이 결정: `LayoutManager`는 화면을 채우는 데 필요한 모든 자식 뷰(`A`, `B`, `C`, `D`, `E`...)의 측정을 완료하면, 이들의 높이 총합을 기반으로 `RecyclerView` 자신이 최종적으로 차지할 크기를 계산하고, `setMeasuredDimension()`을 호출하여 시스템에 보고합니다.

> {style="note"}
> **핵심 포인트 (측정 단계)**:
> `wrap_content`를 사용하는 아이템이 많으면, `RecyclerView`는 자신의 최종 크기를 알기 위해 화면에 보일 모든 아이템 뷰를 실제로 생성(`inflate`)하고 데이터를 바인딩한 후, 각각의 내부 콘텐츠까지 모두 측정하는 복잡한 과정을 거쳐야 합니다.
> 
> 이는 초기 로딩 성능에 직접적인 영향을 미칩니다. 특히 `ViewType`이 모두 다르면 `RecycledViewPool`을 통한 `ViewHolder` 재사용의 이점을 전혀 얻지 못하고 매번 `createViewHolder`를 통한 `inflate`가 발생하므로 비용이 더욱 커집니다.

## 3단계: 자식 뷰(`ItemView`) 배치 (`Layout`) 과정

측정 과정이 끝나고 `View` 계층의 모든 뷰들의 크기가 결정되면, 이제 배치(`Layout`) 과정이 시작됩니다.

1.  `RecyclerView.onLayout()`: 측정 과정과 마찬가지로, `RecyclerView`는 이 책임을 `LayoutManager`에게 위임합니다. `LayoutManager.onLayoutChildren()`이 호출됩니다.
2.  `LayoutManager.onLayoutChildren()`: `LayoutManager`는 측정 단계에서 이미 생성하고 측정한 뷰(`A`, `B`, `C`, `D`, `E`...)를 화면에 배치합니다.
    -   '`A`' 아이템 뷰를 (`0`, `0`) 위치에 배치합니다 (`itemViewA.layout(left, top, right, bottom)`).
    -   '`B`' 아이템 뷰를 '`A`' 아이템 뷰 바로 아래, 즉 (`0`, `A`의 높이) 위치에 배치합니다.
    -   '`C`' 아이템 뷰를 '`B`' 아이템 뷰 바로 아래에 배치합니다.
    -   이 과정을 화면에 보이는 모든 아이템(`A`, `B`, `C`, `D`, `E`)에 대해 반복합니다. 이 단계에서는 뷰의 위치와 크기가 최종적으로 확정됩니다.

## 4단계: 뷰 그리기 (`Draw`) 과정

모든 뷰의 크기와 위치가 확정되었으므로, 이제 화면에 실제로 픽셀을 그릴 차례입니다.

1.  `RecyclerView.draw()`: 시스템이 `RecyclerView`의 `draw()` 메서드를 호출합니다. 이 메서드는 배경, 스크롤바 등을 먼저 그립니다.
2.  `RecyclerView.onDraw()`: 특별한 커스텀 드로잉이 없다면 이 부분은 넘어갑니다.
3.  자식 뷰 그리기 (`dispatchDraw`): `RecyclerView`는 자신의 `dispatchDraw()` 메서드를 통해 화면에 보이는 자식 뷰(`A`, `B`, `C`, `D`, `E`)들의 `draw()` 메서드를 순서대로 호출합니다.
4.  `ItemView.draw()`: 각각의 아이템 뷰는 자신의 `draw()` 메서드 내에서 자신의 배경을 그리고, `dispatchDraw()`를 호출하여 자신의 자식 뷰(`TextView`, `ImageView` 등)들의 `draw()` 메서드를 호출합니다.
5.  하드웨어 가속 렌더링: 이 모든 그리기 명령(`draw call`)들은 `DisplayList`라는 형태로 기록되어 렌더링 스레드(`RenderThread`)로 전달됩니다. 렌더링 스레드는 이 명령들을 `GPU`가 이해할 수 있는 그래픽 명령으로 변환하여 `GPU`에 전달하고, 최종적으로 `GPU`가 화면의 픽셀을 색칠하여 우리가 보는 `UI`가 완성됩니다.

## 결론 및 요약

사용자의 시나리오에서 "리스트를 설정할 때부터 모든 뷰가 `draw`될 때까지"의 과정은 다음과 같이 요약할 수 있습니다.

1.  데이터 설정 및 `requestLayout()`: 어댑터에 리스트가 설정되면, `RecyclerView`는 시스템에 "다시 그려줘"라고 요청합니다.
2.  `onMeasure` 시작:
    1.  `LayoutManager`는 화면을 채우기 위해 필요한 아이템들을 파악합니다 (`A`, `B`, `C`, `D`, `E`...).
    2.  아이템 '`A`'에 대해: `RecycledViewPool`이 비어있으므로, `createViewHolder()`를 통해 `item_a.xml`을 `inflate`하고, `bindViewHolder()`를 호출합니다.
    3.  `wrap_content`이므로, '`A`' 뷰 내부의 모든 자식 콘텐츠까지 **재귀적으로 측정(`measure`)**하여 '`A`'의 최종 높이를 계산합니다.
    4.  아이템 '`B`'에 대해: `RecycledViewPool`에 '`B`' 타입 뷰가 없으므로, `item_b.xml`을 `inflate`하고, 바인딩하고, 내부 콘텐츠까지 전부 측정합니다.
    5.  ... (`E`까지 반복) ...
    6.  `LayoutManager`는 측정된 아이템들의 높이 합으로 `RecyclerView`의 최종 높이를 결정합니다.
3.  `onLayout` 시작: `LayoutManager`가 측정된 크기를 바탕으로 `A`, `B`, `C`, `D`, `E` 뷰를 순서대로 화면상의 정확한 위치에 배치합니다.
4.  `onDraw` 시작: 배치된 `A`, `B`, `C`, `D`, `E` 뷰와 그 내부의 콘텐츠들이 순차적으로 `GPU`에 의해 화면에 그려집니다.

이 과정에서 성능 저하가 발생한다면, 가장 유력한 원인은 측정(`onMeasure`) 단계에서 발생하는 반복적인 `inflate`와 `wrap_content`로 인한 복잡한 측정 계산 때문일 가능성이 매우 높습니다. 특히 모든 아이템의 `ViewType`이 다르다는 점이 `ViewHolder` 재사용을 통한 `inflate` 비용 절감 효과를 초기 로딩 시점에는 전혀 볼 수 없게 만드는 핵심 요인입니다.
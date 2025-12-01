# Q39) ConstraintLayout

## ConstraintLayout이란? {#what-is-constraintlayout}

[ConstraintLayout](https://developer.android.com/reference/android/support/constraint/ConstraintLayout#developer-guide)은 Android에서 도입된 유연하고 강력한 레이아웃으로, 여러 레이아웃을 중첩하지 않고도 복잡하고 반응형 UI를 만들 수 있게 해줍니다. 이 레이아웃은 다른 뷰 또는 부모 컨테이너에 상대적인 제약 조건을 사용하여 뷰의 위치와 크기를 정의할 수 있도록 합니다. 이를 통해 깊이 중첩된 뷰 계층 구조의 필요성을 없애고 성능과 가독성을 향상시킵니다.

### ConstraintLayout의 주요 기능 {#key-features-of-constraintlayout}

1. **제약 조건을 사용한 위치 지정**: 뷰는 정렬, 중앙 배치, 고정을 위한 제약 조건을 사용하여 형제 뷰 또는 부모 레이아웃에 상대적으로 배치될 수 있습니다.
2. **유연한 크기 제어**: `match_constraint`, `wrap_content`, 고정 크기와 같은 옵션을 제공하여 반응형 레이아웃을 쉽게 설계할 수 있습니다.
3. **체인 및 가이드라인 지원**: Chains는 뷰를 수평 또는 수직으로 동일한 간격으로 그룹화할 수 있게 하며, guidelines는 고정 또는 백분율 기반 위치에 정렬할 수 있게 합니다.
4. **Barrier 및 그룹화**: Barriers는 참조된 뷰의 크기에 따라 동적으로 조정되며, grouping은 여러 뷰에 대한 가시성 변경을 단순화합니다.
5. **성능 향상**: 여러 중첩 레이아웃의 필요성을 줄여 레이아웃 렌더링 속도를 높이고 앱 성능을 향상시킵니다.

### ConstraintLayout 예시 {#example-of-constraintlayout}

아래 코드는 `TextView`와 `Button`을 포함하는 간단한 레이아웃을 보여줍니다. `Button`은 `TextView` 아래에 위치하며 수평으로 중앙에 배치됩니다.

```xml

<androidx.constraintlayout.widget.ConstraintLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent">

    <TextView
        android:id="@+id/title"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Hello, World!"
        android:layout_marginTop="16dp"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent"/>

    <Button
        android:id="@+id/button"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Click Me"
        app:layout_constraintTop_toBottomOf="@id/title"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent"/>
</androidx.constraintlayout.widget.ConstraintLayout>
```

### ConstraintLayout의 장점 {#advantages-of-constraintlayout}

1. **평탄한 뷰 계층 구조**: 중첩된 `LinearLayout`이나 `RelativeLayout`과 달리, `ConstraintLayout`은 평탄한 계층 구조를 가능하게 하여 렌더링 성능을 향상시키고 레이아웃 관리를 단순화합니다.
2. **반응형 디자인**: 백분율 기반 제약 조건 및 barriers와 같은 도구를 제공하여 다양한 화면 크기와 방향에 맞게 레이아웃을 조정할 수 있습니다.
3. **내장 도구**: Android Studio의 Layout Editor는 시각적 디자인 인터페이스를 통해 `ConstraintLayout`을 지원하므로 제약 조건을 쉽게 만들고 조정할 수 있습니다.
4. **고급 기능**: Chains, guidelines, barriers는 추가 코드나 중첩 레이아웃 없이 복잡한 UI 디자인을 단순화합니다.

### ConstraintLayout의 한계 {#limitations-of-constraintlayout}

1. **간단한 레이아웃의 복잡성**: `LinearLayout`이나 `FrameLayout`으로 충분한 간단한 레이아웃에는 과도하게 복잡할 수 있습니다.
2. **학습 곡선**: 제약 조건 및 고급 기능에 대한 이해가 필요하므로 초보자에게는 어려울 수 있습니다.

### ConstraintLayout 활용 사례 {#use-cases-of-constraintlayout}

1. **반응형 UI**: 다양한 화면 크기에 걸쳐 정확한 정렬과 적응성이 필요한 디자인에 이상적입니다.
2. **복잡한 레이아웃**: 여러 겹치는 요소나 복잡한 위치 지정 요구 사항이 있는 UI에 적합합니다.
3. **성능 최적화**: 중첩된 뷰 계층 구조를 단일 평탄 구조로 대체하여 레이아웃 최적화에 도움이 됩니다.

### 요약 {#summary}

`ConstraintLayout`은 Android UI를 설계하기 위한 다재다능하고 효율적인 레이아웃입니다.
중첩 레이아웃의 필요성을 없애고, 위치 지정 및 정렬을 위한 고급 도구를 제공하며, 성능을 향상시킵니다.
학습 곡선이 있을 수 있지만, `ConstraintLayout`을 숙달하면 개발자는 반응형이고 시각적으로 매력적인 레이아웃을 효율적으로 만들 수 있습니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) ConstraintLayout은 중첩된 LinearLayout 및 RelativeLayout에 비해 성능을 어떻게 향상시키나요? ConstraintLayout을 사용하는 것이 더 효율적인 시나리오를 제시하세요.">

기존 레이아웃의 가장 큰 성능 병목은 뷰의 크기와 위치를 계산하는 **Measure(측정) 단계**에서 발생합니다. 

* 중첩된 레이아웃의 문제점
  * `LinearLayout`에서 `layout_weight`를 사용하거나, `RelativeLayout`을 사용할 경우, 자식 뷰의 크기를 정확히 계산하기 위해 최소 2번 이상의 측정(Measure) 과정이 필요합니다. 
  * 이러한 레이아웃이 깊게 중첩되면, 상위 뷰의 재측정이 하위로 전파되면서 측정 횟수가 기하급수적으로 늘어납니다. 이를 "이중 과세"라고 합니다.
  * 예를 들어, 2번 측정하는 레이아웃이 3단계로 중첩되면 $2 x 2 x 2 = 8$번 이상의 측정이 발생할 수 있습니다.

* ConstraintLayout의 해결책
  * 단일 계층 구조: ConstraintLayout은 자식 뷰 간의 상호 제약 조건을 사용하여 복잡한 배치를 중첩 없이 하나의 계층 안에서 해결합니다.
  * Cassowary 알고리즘: 내부적으로 선형 방정식 풀이 알고리즘(Cassowary linear arithmetic solver)을 사용하여 각 뷰의 위치와 크기를 효율적으로 계산합니다. 이를 통해 뷰 계층 깊이를 획기적으로 줄여 렌더링 파이프라인의 오버헤드를 감소시킵니다.

**ConstraintLayout이 더 효율적인 시나리오**

1. 복잡한 화면 구성

여러 검포넌트가 서로 복잡하게 얽혀 있는 화면을 구현할 때

* 기존: `RelativeLayout`안에 `LinearLayout`을 넣고, 다시 그 안에 `LinearLayout`을 넣는 식의 깊은 중첩이 발생합니다.
* 개선: `ConstraintLayout` 하나만 사용하여 모든 자식 뷰를 배치할 수 있어 뷰 계층을 1단계로 유지할 수 있습니다.

2. RecyclerView 아이템 레이아웃

리스트 형태의 UI는 스크롤 시 수십 번씩 뷰홀더가 생성되고 바인딩됩니다. 

* 효율성: 아이템 레이아웃의 깊이가 깊을수록 XML을 자바/코틀린 객체로 만드는 Inflation 시간과 레이아웃을 계산하는 Measure 시간이 길어집니다. ConstraintLayout으로 아이템 뷰의 계층을 평탄화하면 스크롤 버벅임을 줄이는 데 큰 도움이 됩니다.

3. 비율(Ratio) 및 가중치(Weight) 기반 배치가 필요한 경우

* 기존: `LinearLayout`의 `layout_weight`는 성능 비용이 높습니다. 
* 개선: `ConstraintLayout`은 `layout_constraintDimensionRatio`나 Chains 기능을 통해 성능 저하 없이 유연한 비율 설정과 분할 배치가 가능합니다.

4. 뷰의 겹침 처리가 필요한 경우

* 기존: `FrameLayout`이나 `RelativeLayout`을 조합해야 하며, Z-ordering(앞뒤 순서) 관리가 복잡해질 수 있습니다.
* 개선: `ConstraintLayout`은 제약 조건만으로 뷰를 쉽게 겹치게 배치할 수 있으며, 렌더링 순서 제어가 용이합니다.

**언제 사용하면 안 되는가?**

`ConstraintLayout`이 항상 정답은 아닙니다. 단순한 UI에서는 오히려 오버헤드가 될 수 있습니다.

* 단순한 일렬 배치: 아이콘 옆에 텍스트 하나가 있는 단순한 구조라면 LinearLayout이나 FrameLayout이 훨씬 가볍고 빠릅니다. ConstraintLayout은 초기화 시 솔버(Solver)를 로드하는 비용이 있기 때문입니다.

</def>
<def title="Q) ConstraintLayout에서 match_constraint (0dp) 동작이 어떻게 작동하는지 설명하세요. wrap_content 및 match_parent와 어떻게 다르며, 어떤 상황에서 사용해야 하나요?">

`ConstraintLayout`에서 `android:layout_width="0dp"` 또는 `android:layout_height="0dp"`로 설정하는 것을 `match_constraint`라고 합니다.

이 설정은 `ConstraintLayout`의 가장 강력한 기능 중 하나로, 뷰의 크기를 콘텐츠가 아닌 제약 조건에 맞춰 유동적으로 결정하겠다는 의미입니다.

1. `match_constraint` (`0dp`) 의 동작 원리

`0dp`는 "크기가 0이다"라는 뜻이 아니라, "제약 조건이 연결된 구간(앵커)까지 뷰를 늘려서 채워라"라는 지시어입니다. 
* 뷰의 양쪽(좌/우 또는 상/하)에 제약 조건이 걸려 있다면, `0dp`는 뷰를 양쪽 앵커에 닿을 때까지 코무줄처럼 팽팽하게 늘립니다. 
* `ConstraintLayout`은 먼저 제약 조건을 계산하고, 남는 공간을 `0dp`로 설정된 뷰에게 할당합니다.

2. `wrap_content` 및 `match_parent` 와의 비교

* **`wrap_content`**: 텍스트나 이미지 등 자신의 내용을 크기만큼만 공간을 차지합니다. 제약 조건은 위치(정렬)을 잡는 데만 사용됩니다.
* **`match_parent`**: 부모 컨테이너의 전체 크기를 가득 채웁니다.
* **`match_constraint` (`0dp`)**: 연결된 제약 조건 사이의 거리만큼 뷰의 크기를 결정합니다. 마진을 제외한 나머지 공간을 모두 채웁니다.

</def>
</deflist>
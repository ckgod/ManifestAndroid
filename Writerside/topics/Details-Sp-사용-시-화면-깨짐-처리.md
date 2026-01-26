# Details: Sp 사용 시 화면 깨짐 처리

## Sp 단위를 사용할 때 화면 깨짐 현상을 어떻게 처리하시겠습니까?

Sp(Scale-independent Pixels) 단위는 화면 밀도와 사용자 글꼴 기본 설정에 따라 크기가 조정되므로 Android에서 텍스트 접근성을 보장하는 데 중요합니다. 
하지만 사용자가 설정한 큰 글꼴 크기로 인해 과도한 스케일링이 발생하면 UI 컴포넌트가 겹치거나 화면을 벗어나는 레이아웃 깨짐 문제가 발생할 수 있습니다. 
사용자 친화적인 경험을 유지하려면 이러한 시나리오를 적절하게 처리하는 것이 필수적입니다.

## 화면 깨짐 방지 전략 {#screen-breaking-prevention-strategies}

사용자가 시스템 글꼴 크기를 크게 늘리면 Sp 단위로 인해 텍스트 요소가 의도된 경계를 넘어 확장될 수 있습니다. 
이는 버튼, 레이블 또는 컴팩트한 화면과 같이 제한된 공간에서 특히 레이아웃을 깨뜨릴 수 있습니다.

### 1. 콘텐츠를 적절하게 래핑 {#wrap-content-properly}

TextView 또는 Button과 같은 텍스트 기반 컴포넌트의 크기가 `wrap_content`로 설정되어 있는지 확인하세요. 
이렇게 하면 컨테이너가 텍스트 크기에 따라 동적으로 확장되어 텍스트 잘림이나 오버플로를 방지할 수 있습니다.

```xml
<TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:textSize="16sp"
        android:text="Sample Text" />
```

### 2. TextView에 minLines 또는 maxLines 사용 {#use-minlines-maxlines}

텍스트 확장 동작을 제어하려면 `minLines` 및 `maxLines` 속성을 사용하여 레이아웃을 방해하지 않고 텍스트가 읽기 가능한 상태를 유지하도록 하세요. 
이를 `ellipsize`와 결합하여 오버플로를 처리할 수 있습니다.

```xml
<TextView
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:textSize="16sp"
    android:maxLines="2"
    android:ellipsize="end"
    android:text="This is a long sample text that might break the layout if not handled properly." />
```

### 3. 중요한 UI 컴포넌트에 고정 크기 사용 {#use-fixed-sizes}

일관된 크기가 필수적인 경우, 버튼과 같은 중요한 컴포넌트에 Dp를 사용하는 것을 고려하세요. 
이렇게 하면 텍스트 스케일링과 상관없이 컴포넌트 크기가 안정적으로 유지됩니다. 
이러한 컴포넌트 내의 텍스트 크기에는 Sp를 최소한으로 사용하여 깨짐을 최소화하세요.

```xml
<Button
    android:layout_width="100dp"
    android:layout_height="50dp"
    android:textSize="14sp"
    android:text="Button" />
```

### 4. 극단적인 글꼴 크기로 테스트 {#test-extreme-font-sizes}

항상 기기 설정에서 사용할 수 있는 가장 큰 시스템 글꼴 크기로 앱을 테스트하세요. 
깨지거나 겹치는 UI 컴포넌트를 식별하고, 더 큰 텍스트를 수용하도록 레이아웃을 개선하세요.

### 5. Constraint를 사용한 동적 크기 조절 고려 {#dynamic-sizing-constraints}

ConstraintLayout을 사용하여 컴포넌트의 위치 지정 및 크기 조절에 유연성을 더하세요. 
텍스트가 확장되더라도 다른 UI 요소와 겹치지 않도록 텍스트 요소에 대한 Constraint를 정의하세요.

```xml
<ConstraintLayout
    android:layout_width="match_parent"
    android:layout_height="wrap_content">

<TextView
    android:id="@+id/sampleText"
    android:layout_width="0dp"
    android:layout_height="wrap_content"
    android:textSize="16sp"
    app:layout_constraintStart_toStartOf="parent"
    app:layout_constraintEnd_toEndOf="parent"
    app:layout_constraintTop_toTopOf="parent"
    android:text="Dynamic Layout Example" />
</ConstraintLayout>
```

### 6. Sp 대신 Dp 크기 사용 {#use-dp-instead-of-sp}

이것은 주로 팀의 접근 방식에 따라 달라집니다. 
일부 회사는 사용자 조정 글꼴 크기로 인한 레이아웃 문제를 방지하기 위해 텍스트 크기에 Sp 대신 Dp를 사용하기도 합니다. 
그러나 Sp는 접근성을 지원하고 사용자의 읽기 용이성 선호도에 따라 텍스트가 조정되도록 특별히 설계되었으므로, 이 접근 방식은 사용자 경험을 저해할 수 있습니다.

## 요약 {#summary}

Sp로 인한 화면 깨짐을 처리하려면 `wrap_content` 사용, Constraint 설정, 텍스트 확장 제한 정의와 같은 모범 사례를 결합하십시오. 
극단적인 글꼴 크기로 테스트하고 레이아웃을 동적으로 관리하면 앱이 모든 사용자에게 시각적으로 일관되고 접근 가능하도록 유지됩니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 텍스트 크기에 Sp를 사용할 때 발생할 수 있는 레이아웃 깨짐 문제는 무엇이며, 이를 어떻게 방지할 수 있습니까?">

시스템 글꼴 크기를 '가장 크게' 등으로 설정했을 때 문제가 발생합니다. 

1. 텍스트 잘림: 텍스트를 감싸는 컨테이너(ViewGroup)나 TextView 자체에 고정 높이를 설정한 경우, 폰트 크기가 커지면 텍스트가 영역 밖으로 넘치거나 잘려 보입니다.
2. 뷰 겹침: `ConstraintLayout`이나 `RelativeLayout`에서 뷰 간의 제약 조건이 유동적인 크기 변화를 고려하지 않고 고정된 마진이나 위치로 설정된 경우, 커진 텍스트 뷰가 인접한 다른 뷰(아이콘, 버튼)를 덮어버립니다.
3. 줄바꿈으로 인한 레이아웃 파괴: 단일 라인으로 예상했던 텍스트가 크기 증가로 인해 두 줄 이상으로 늘어나면서, 하단에 위치한 뷰들을 밀어내거나 화면 밖으로 이탈시킵니다.

**해결법**

1. 레이아웃 구조적 개선
   * 고정된 수치 대신 관계 중심의 제약 조건을 사용한다. (`wrap_content` 사용)
   * `minHeight` 사용
   * `ConstraintLayout`의 `Barrier`활용
2. TextView 속성 제어
   * `ellipsize`와 `maxLines`: 텍스트가 지정된 줄 수를 초과할 경우 말줄임표(..)로 처리하여 레이아웃이 무너지는 것을 막습니다.
   * Autosizing TextView: 공간은 고정되어야 하고 텍스트 내용은 모두 보여야 한다면, 폰트 크기를 자동으로 줄이는 기능을 사용합니다. (폰트가 너무 작아져 가독성을 해칠 수 있으므로`autoSizeMinTextSize` 설정 필요)

</def>
</deflist>
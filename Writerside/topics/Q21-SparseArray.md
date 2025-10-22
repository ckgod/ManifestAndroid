# Q21) SparseArray

## SparseArray 사용의 장점은 무엇인가요? {#14555}
**`SparseArray`** (`android.util` package)는 `HashMap`과 유사하게 정수 `key`를 객체 `value`에 매핑하는 `Android`의 데이터 구조입니다. 그러나 `integer`인 `key`와 함께 사용하도록 최적화되어 있어, 정수 기반 `key`를 사용할 때 일반 `Map`이나 `HashMap`보다 메모리 효율적인 대안이 됩니다.

### SparseArray의 주요 특징 {#145144155}
1.  **메모리 효율성**: `key-value` 매핑을 위해 `HashTable`을 사용하는 `HashMap`과 달리, `SparseArray`는 `auto-boxing` (기본형 `int`를 `Integer`로 변환)을 피하고 `Entry objects`와 같은 추가 데이터 구조에 의존하지 않습니다. 이로 인해 메모리를 훨씬 적게 소비합니다.
2.  **성능**: 매우 큰 데이터 세트의 경우 `HashMap`만큼 빠르지는 않지만, `SparseArray`는 메모리 최적화 덕분에 중간 규모의 데이터 세트에서 더 나은 성능을 제공합니다.
3.  **`null key` 불허**: `SparseArray`는 `primitive integers`를 `key`로 사용하므로 `null key`를 허용하지 않습니다.

`SparseArray`의 사용법은 `Android`의 다른 `map`과 유사한 구조와 마찬가지로 간단합니다.


```kotlin
    // import android.util.SparseArray
    
    val sparseArray = SparseArray<String>()
    sparseArray.put(1, "One")
    sparseArray.put(2, "Two")
    
    // Accessing elements
    val value = sparseArray[1] // "One"
    
    // Removing an element
    sparseArray.remove(2)
    
    // Iterating over elements
    for (i in 0 until sparseArray.size()) {
        val key = sparseArray.keyAt(i)
        val value = sparseArray.valueAt(i)
        println("Key: $key, Value: $value")
    }
```

### `Array` 또는 `HashMap`보다 `SparseArray`를 사용하는 이점
1.  **`Auto-Boxing` 방지**: `HashMap<Integer, Object>`에서 `key`는 `Integer object`로 저장되어 `boxing` 및 `unboxing` 작업으로 인한 오버헤드가 발생합니다. `SparseArray`는 `int key`를 직접 사용하여 메모리 및 계산 노력을 절약합니다.
2.  **메모리 절약**: `SparseArray`는 `key`와 `value`를 저장하기 위해 내부적으로 `primitive array`를 사용하여 `Entry`와 같은 여러 객체를 생성하는 `HashMap` 구현에 비해 메모리 공간을 줄입니다.
3.  **콤팩트한 데이터 저장**: 적은 수의 `key-value pair`를 가진 스파스 데이터 세트나 `key`가 넓은 범위의 `integer`에 걸쳐 드문드문 분포된 데이터 세트에 적합합니다.
4.  **`Android` 전용 설계**: 제한된 리소스 시나리오를 처리하기 위해 `Android`용으로 특별히 설계되었으며, `Android UI components`에서 `View ID`를 객체에 매핑하는 것과 같은 사용 사례에 특히 효과적입니다.

### SparseArray의 한계
`SparseArray`는 메모리 효율적이지만, 모든 사용 사례에 항상 최선의 선택은 아닙니다:
1.  **성능 절충**: `SparseArray`에서 요소에 접근하는 것은 `key lookup`을 위해 `binary search`를 사용하기 때문에 매우 큰 데이터 세트의 경우 `HashMap`보다 느립니다.
2.  **정수 `Key`만 가능**: `integer key`로 제한되어 다른 유형의 `key`가 필요한 사용 사례에는 적합하지 않습니다.

### 요약
`SparseArray`는 `Android`에서 `integer key`를 `object value`에 매핑하기 위한 특수 데이터 구조로, 메모리 효율성에 최적화되어 있습니다. `auto-boxing`을 피하고 메모리 사용량을 줄이는 측면에서 `HashMap`보다 상당한 이점을 제공하며, 특히 `integer key`를 가진 데이터 세트에 유용합니다. 일부 성능을 메모리 절약과 맞바꿀 수 있지만, `Android application`과 같이 리소스가 제한된 사용 사례에는 탁월한 선택입니다.

> Q) 일반적인 `HashMap` 대신 `SparseArray`를 사용하는 것을 선호하는 시나리오는 무엇이며, `성능`과 `사용성` 측면에서 어떤 절충점이 있나요?
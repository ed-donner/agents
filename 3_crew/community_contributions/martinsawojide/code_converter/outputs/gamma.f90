PROGRAM OMP_MAX_SUBARRAY
  USE OMP_LIB
  IMPLICIT NONE

  INTEGER(8), PARAMETER :: N = 3000
  INTEGER(8), PARAMETER :: INITIAL_SEED = 42
  INTEGER(8), PARAMETER :: MIN_VAL = -10
  INTEGER(8), PARAMETER :: MAX_VAL = 10
  INTEGER(8), PARAMETER :: RUNS = 20

  INTEGER(8) :: i, j, k, seed, total_sum
  INTEGER(8) :: count_rate, count_start, count_end
  REAL(8) :: elapsed_time
  INTEGER(8), ALLOCATABLE :: arr(:)
  INTEGER(8) :: current_lcg_seed

  ALLOCATE(arr(N))

  CALL SYSTEM_CLOCK(count_start, count_rate)

  total_sum = 0
  current_lcg_seed = INITIAL_SEED

  !$OMP PARALLEL DO PRIVATE(seed, arr, i, j, k, current_lcg_seed) REDUCTION(+:total_sum)
  DO k = 1, RUNS
     seed = current_lcg_seed
     ! Advance LCG to match Python generation per run
     DO i = 1, k
        seed = MOD(1664525_8 * seed + 1013904223_8, 2_8**32)
     END DO

     ! Generate random numbers for this instance
     DO i = 1, N
        seed = MOD(1664525_8 * seed + 1013904223_8, 2_8**32)
        arr(i) = MOD(seed, (MAX_VAL - MIN_VAL + 1)) + MIN_VAL
     END DO

     ! Max subarray sum algorithm (O(N^2))
     BLOCK
        INTEGER(8) :: local_max_sum, current_sum, inner_i, inner_j
        local_max_sum = -999999999999_8
        DO inner_i = 1, N
           current_sum = 0
           DO inner_j = inner_i, N
              current_sum = current_sum + arr(inner_j)
              IF (current_sum > local_max_sum) THEN
                 local_max_sum = current_sum
              END IF
           END DO
        END DO
        total_sum = total_sum + local_max_sum
     END BLOCK
  END DO
  !$OMP END PARALLEL DO

  CALL SYSTEM_CLOCK(count_end, count_rate)
  elapsed_time = REAL(count_end - count_start, 8) / REAL(count_rate, 8)

  PRINT *, "Total Maximum Subarray Sum (20 runs):", total_sum
  WRITE(*, '(A, F10.6, A)') "Execution Time: ", elapsed_time, " seconds"

  DEALLOCATE(arr)
END PROGRAM OMP_MAX_SUBARRAY
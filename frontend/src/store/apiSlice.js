import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export const apiSlice = createApi({
   reducerPath: 'api',
   baseQuery: fetchBaseQuery({
      baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
   }),
   tagTypes: ['Contacts', 'Events'],
   endpoints: (builder) => ({
      // Теперь принимает month и year для фильтрации в БД
      getContacts: builder.query({
         query: (params) => ({
            url: '/contacts',
            params: {
               month: params?.month, // Передаем 01, 02...
               year: params?.year, // Передаем 2026...
            },
         }),
         providesTags: ['Contacts'],
      }),

      // Эндпоинт для обновления прогресса (книга/страница)
      updateProgress: builder.mutation({
         query: ({ id, ...patch }) => ({
            url: `/contacts/${id}`,
            method: 'PATCH',
            body: patch,
         }),
         invalidatesTags: ['Contacts'],
      }),

      // НОВЫЙ: Запись на урок (создание события в БД)
      addLesson: builder.mutation({
         query: (lessonData) => ({
            url: '/lessons',
            method: 'POST',
            body: lessonData, // { student_id, date, time, topic }
         }),
         // Инвалидируем контакты, чтобы на календаре сразу появилась точка
         invalidatesTags: ['Contacts', 'Events'],
      }),
   }),
});

export const {
   useGetContactsQuery,
   useUpdateProgressMutation,
   useAddLessonMutation,
} = apiSlice;

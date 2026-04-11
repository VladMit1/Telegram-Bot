import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export const apiSlice = createApi({
   reducerPath: 'api',
   baseQuery: fetchBaseQuery({
      baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
   }),
   tagTypes: ['Contacts', 'Events'],
   endpoints: (builder) => ({
      getContacts: builder.query({
         query: () => '/contacts',
         providesTags: ['Contacts'],
      }),
      // Эндпоинт для обновления прогресса (книга/страница)
      updateProgress: builder.mutation({
         query: ({ id, ...patch }) => ({
            url: `/contacts/${id}`,
            method: 'PATCH',
            body: patch,
         }),
         invalidatesTags: ['Contacts'], // Автоматически обновит список в App
      }),
   }),
});

export const { useGetContactsQuery, useUpdateProgressMutation } = apiSlice;

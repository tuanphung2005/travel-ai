---
title: Travel Ai
emoji: 📉
colorFrom: yellow
colorTo: purple
sdk: docker
pinned: false
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
places:
[
  {
    _id: ObjectId('6953524453ece5575927223a'),
    google_id: 'ChIJSXwdOKOrNTERNylYj9mnIbU',
    name: 'Hoàng Thành Thăng Long',
    description: 'Hoàng thành từ thế kỷ 11. Khu hoàng thành với các tòa nhà và tác phẩm điêu khắc có từ thế kỷ 11, gồm một tòa tháp và con rồng đá.',
    category: 'ATTRACTION',
    address: '19c Hoàng Diệu, Điện Biên, Ba Đình, Hà Nội 100000, Việt Nam',
    location: { type: 'Point', coordinates: [ 105.8402594, 21.0352231 ] },
    images: [
      'https://res.cloudinary.com/dkshpgp3n/image/upload/v1767068066/berotravel/hanoi_places/ChIJSXwdOKOrNTERNylYj9mnIbU.jpg'
    ],
    ownerId: 'SYSTEM_CRAWLER',
    rating: 4.4,
    reviewCount: 17842,
    priceLevel: 0,
    tags: [ 'địa điểm du lịch', 'hoàn kiếm' ],
    status: 'APPROVED',
    createdBy: 'ADMIN_CRAWLER',
    createdAt: ISODate('2025-12-30T04:17:08.475Z'),
    updatedAt: ISODate('2025-12-30T04:17:08.475Z')
  }
]

journey

Atlas atlas-wag5gg-shard-0 [primary] berotravel> db.journeys.find().limit(1).pretty()
[
  {
    _id: ObjectId('6965ac017591cb43d71ed462'),
    name: 'Hành trình khám phá Phú Thọ',
    owner_id: '6965abb87591cb43d71ed461',
    members: [ '6965abb87591cb43d71ed461' ],
    start_date: ISODate('2026-01-15T00:00:00.000Z'),
    end_date: ISODate('2026-01-17T00:00:00.000Z'),
    days: [
      { day_number: 1, date: ISODate('2026-01-15T00:00:00.000Z'), stops: [] },
      { day_number: 2, date: ISODate('2026-01-16T00:00:00.000Z'), stops: [] },
      { day_number: 3, date: ISODate('2026-01-17T00:00:00.000Z'), stops: [] }
    ],
    total_budget: 0,
    status: null,
    created_at: ISODate('2026-01-13T02:20:49.534Z'),
    updated_at: ISODate('2026-01-13T02:20:49.534Z')
  }
]